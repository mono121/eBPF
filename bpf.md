# eBPF

## eBPFとは

eBPF(extended Berkeley Packet Filter)はカーネルが提供する機能の一つで。カーネル空間で動作するVMにBPFバイトコードを実行し、カーネルイベントをフックし、それらをユーザ空間のアプリケーションへ通知、データ共有が可能。
パフォーマンス観点では、不要なパケットデータのコピーやカーネルとユーザモードのコンテキストスイッチ（対象を切り替えること）を削減することが可能であるため、パフォーマンスを大幅に向上させることが可能

### カーネル空間とユーザ空間

カーネル空間：カーネルが使用するメモリ領域
ユーザ空間：OS上で動作するソフトウェアが使用するメモリ領域

## カーネルプローブ

カーネルプローブは Linux カーネルのデバッグや性能に関する情報を収集するためのツール集。

## 大まかな処理フロー
1. eBPFのプログラムをコンパイルしてeBPFバイトコードに変換 (libbccやlibbpfなどのライブラリの中でコンパイラを呼び出して利用している)
2. システムコールを利用してeBPFバイトコードをカーネル空間にロード
3. eBPF VefifierがeBPFバイトコードの安全性をチェック
4. eBPFのバイトコードの安全性に問題がなければ、JITコンパイラで機械語にコンパイル
5. フロントエンドのプログラムが目的（プローブ対象）のイベントにアタッチ
6. 目的のイベントが発生するとその対象コードをExecutorが実行
7. モニタリング結果をユーザプログラムとの共有スペース（map, ring buffer等）に格納
8. ユーザプログラム側で必要に応じて結果を参照利用

### BPF CO-RE

eBPFのソースコードはカーネルヘッダを参照するため、ビルドホストとターゲットホストのカーネルバージョンを合わせなければいけない。これを解決するための仕組みがBPF CO-RE（Compile Once - Run Everywhere）。eBPFのバイトコードを書き換えるために必要な情報を管理する仕組みをBTFと呼ぶ。

### ツール

・BCC
eBPFのバイトコードを提供するコンパイラ、eBPFツールとして利用するときのフロントエンドの環境 (メインはPython、その他にC++, Luaをサポート) 、eBPFを利用してよく作られる便利なツール類をサンプルコマンドとしてまとめて提供してる。

・bpftrace / SystemTap
一般的にeBPFを利用する場合には、eBPF本体のプログラムとトレーシング用のフロントエンドのユーザランド側の2つのプログラムを用意する必要がある。しかし、bpftraceでは独自のスクリプト言語 (DSL) とコマンドラインツールを提供することで、カーネルサイドとユーザサイドを意識することなくより簡単に一つのプログラムでトレーシング処理を記述することが可能。bpftraceはSystemTapの後継。

・perf-tools


・ply

・bpfilter
BPFを利用することでFirewallを実現するというLinuxカーネルのプロジェクト。

・seccomp
seccomp (SECure COMPuting with filters) はサンドボックスを実現するためにプロセスのシステムコールの発行を制限するための機能を実現する。内部ではシステムコールのフィルタリングにcBPFを利用してる。

### 注意点

・ソフトウェアライセンス
ユーザが作成したソースコードはGPL-2にしないとプログラムがロードされない。

・制約
命令数の制限
    扱える上限命令数がLinuxカーネルv5.4で1M個程度。
ループ上限
    Linuxカーネルv5.3以降から有限回数のループが許可された。

## 実装

### 実行環境

・VMware Workstation 16 Player
・OS：CentOS Stream 8
・kernel：4.18.0-408.el8.x86_64
・memory：4GB
・cpu：Intel(R) Core(TM) i5-6500 CPU @ 3.20GHz core 1
・storage：20GB 

### kernel version up(今回はdevel,headersのバージョン合わせるのめんどくさいからパス)

```
rpm --import https://www.elrepo.org/RPM-GPG-KEY-elrepo.org
yum install https://www.elrepo.org/elrepo-release-8.el8.elrepo.noarch.rpm

#最新安定版をインストールする場合
$ yum --enablerepo=elrepo-kernel install kernel-ml

#長期サポート版をインストールする場合
$ yum --enablerepo=elrepo-kernel install kernel-lt
```

### config

BPFをしようするための最低限のconfig。`/boot/config-<kernel-version>`で設定する。
```
CONFIG_BPF=y
CONFIG_BPF_SYSCALL=y
CONFIG_BPF_JIT=y
CONFIG_HAVE_EBPF_JIT=y
```

## BCC

### bcc install

kernelのバージョンが4.1以上じゃなきゃだめ。また、カーネルは次のフラグを設定してコンパイルされている必要がある。
この環境だと最後の行の`CONFIG_IKHEADERS`が`CONFIG_IKHEADERS is not set`になっていたので`CONFIG_IKHEADERS=y`に変更した。

``` shell
CONFIG_BPF=y
CONFIG_BPF_SYSCALL=y
# [optional, for tc filters]
CONFIG_NET_CLS_BPF=m
# [optional, for tc actions]
CONFIG_NET_ACT_BPF=m
CONFIG_BPF_JIT=y
# [for Linux kernel versions 4.1 through 4.6]
CONFIG_HAVE_BPF_JIT=y
# [for Linux kernel versions 4.7 and later]
CONFIG_HAVE_EBPF_JIT=y
# [optional, for kprobes]
CONFIG_BPF_EVENTS=y
# Need kernel headers through /sys/kernel/kheaders.tar.xz
CONFIG_IKHEADERS=y
```

バニラカーネルでbccネットワークを実行するためには次のオプションも必要。こっちはデフォで全部設定されていた。
 ``` 
CONFIG_NET_SCH_SFQ=m
CONFIG_NET_ACT_POLICE=m
CONFIG_NET_ACT_GACT=m
CONFIG_DUMMY=m
CONFIG_VXLAN=m
 ```

bccのインストール
`yum install bcc-tools`

### hello world

``` python
#!/usr/bin/python

from bcc import BPF

BPF(text='int kprobe__sys_clone(void *ctx) { bpf_trace_printk("Hello, World!\\n"); return 0; }').trace_print()
```

"""の中がC言語で書かれたBPFプログラム。関数名は「イベント名__関数名」という書式で、カーネルの任意の関数のイベントをフックして処理を追加できる。このタイプで記述できるイベントは「kprobes」と「kretprobes」の2種類で、前者が関数が呼び出される前に実行されるイベントで、後者が関数から戻る時に実行されるイベント。

## bpftrace

### bpftrace install

Fedora 28 (and later)からはインストール済み
`sudo dnf install -y bpftrace`

## ツール作成手順

### 1. 何のツールを作成するか決める

書籍2のPart Ⅱ: Using BPF toolsの各章末にトレーシングに関する練習問題が挙げられており、一部の問題は指示されたツールの開発である。この問題に取り組んでみるのもいいかもしれない。例えば、8.5 "Optional Exercises"のリストの3-7番目はツール開発の問題である。そのうちの4番目がおもしろそうなので、以下に引用しておく。
"4. Develop a tool to show the ratio of logical file system I/O (via VFS or the file system interface) vs physical I/O (via block tracepoints)."

### 2.トレージング対象の探索

kprobesとtracepointsでカーネル内のフックポイントのリストを出力し、トレース可能な対象を概観する。kprobesでアタッチ可能な関数のリストは、/sys/kernel/debug/tracing/available_filter_functionsから読み出せる。
tracepointsのリストはbcc toolsに含まれるtplist(8)の出力から得られる。システムコールはtracepointsに含まれる。

実際にカーネルに負荷を発生させながら、その負荷に関連するイベントソースを調べる方法がある。bcc toolsのprofile(8) では、-pオプションでPIDを指定することにより、動作中のプロセスに紐づくスタックトレースを取得できる。スタックトレースからフックポイントとして使えそうなものを発見できるかもしれない。その他のスタックトレースや関数の呼び出し回数を出力するツールは、funccount(2) メモリであればmemleak(8)、ファイルシステムであればxfsdist(8)、ext4dist(8)、ディスクI/Oであれば、biostacks(8)、ネットワークの上位層のソケット層では、sockstat(8)がある。bcc tools以外では、ネットワークの下位層のパケットに対しては、@YutaroHayakawaさん作のipftrace2も有用である。ipftrace2はカーネル内のパケットのフローを関数単位で追跡できる。

フックポイントに見当をつけたのちに、そのフックポイントの詳細を調べる。まず、tplist(8)により、フックポイントの引数の名前と型を確認する。

次に、argdist(8)により引数の値と返り値の分散を確認できる。フックポイントの通過頻度が小さければ、trace(8)で個々のイベントを出力することもできる。最後に、bpftraceを使用してフックポイントに対して簡単に処理を書いてみることもできる。bpftraceのリファレンスガイドにあるように、さまざまなユーティリティ関数が揃っている。

### 3. BCCによるプロトタイピング

bccリポジトリ内の性能分析ツールが非推奨になったとはいえ、BCCはプロトタイピングに有用だ。BCCであれば、BPFプログラムとフロントエンドプログラムの両方を1枚のスクリプト内に収められるため、試行錯誤を速められる。例えば、BPFプログラムはPythonの文字列として記述されるため、フロントエンドへの入力に応じて、文字列処理で簡単にBPFプログラムを動的生成できる。mapへのアクセスも、libbpfを直接使うより簡単に書ける。 BCCの機能は、BCCのリファレンスガイドに整理されている。

### 4. libbpf + CO-RE

NakryikoによるBuilding BPF applications with libbpf-bootstrapの記事にlibbpfベースのBPFアプリケーションの構築方法がまとめられている。同時に、libbpf + Cに移植されたbcc toolsのソースコードが具体例として参考になる。これらのリソースがなければ、著者は実装がおぼつかなかっただろう。ただし、Nakryikoの記事は古いバージョンのlibbpfを基に書かれているため、libbpf 1.0以降では一部のAPIの仕様が変更されていることに留意しなければならない。

BPFは開発が活発なため、カーネルの細かなバージョンごとに利用可能な機能に差異がある。BPFの機能とカーネルバージョンとの対応表があるため、サポートするカーネルバージョンを決めてからどの機能を利用するかを見当するとよい。

余談だが、CO-REの機構を使わずに、異なるカーネルバージョンに対応する方法もなくはない。weaveworks/tcptracer-bpfでは、既知のパラメータ（既知のIPアドレスやポートなど）で一連のTCP接続を作成し、それらのパラメータがカーネルのstruct sock構造体のフィールドオフセットを検出している。datadog-agentでも

## XDP tutorial



## 参考資料

・[Brendan Gregg's Blog](https://www.brendangregg.com/blog/2016-03-05/linux-bpf-superpowers.html){:target="_blank"}

・[公式のBPFドキュメント](https://www.kernel.org/doc/Documentation/networking/filter.txt){:target="_blank"}

・[cilium公式のBPFドキュメント](https://docs.cilium.io/en/latest/bpf/){:target="_blank"}

・[公式じゃないけどわかりやすいBPFドキュメント](https://www.kernel.org/doc/html/latest/bpf/index.html){:target="_blank"}

・[BCCのソースコード](https://github.com/iovisor/bcc){:target="_blank"}

・[bpftraceのソースコード](https://github.com/iovisor/bpftrace){:target="_blank"}

・[perfのソースコード](https://github.com/brendangregg/perf-tools){:target="_blank"}

・[seccompのソースコード](https://github.com/seccomp){:target="_blank"}

・[eBPFのはじめかた](https://speakerdeck.com/chikuwait/learn-ebpf{:target="_blank"}

・[aya](https://github.com/aya-rs/aya{:target="_blank"}

## 用語集

・JITコンパイラ
    ソフトウェアの実行時に環境に依存しない中間コードを機械語にコンパイルするため、「実行時コンパイラ」とも呼ばれている。 「Java VM」や「HotSpot」などがその代表格。 JITコンパイラは近年、多くのプログラミング言語における高速化技術として必要不可欠になっている。
・カーネルモジュール
    カーネルの機能を拡張するためのバイナリファイル。
・LLVM/Clang
    Low Level Virtual Machine (低水準仮想機械) の略で、中間言語を介して、対象のアーキテクチャに最適なマシン語へ変換する。Clangは、プログラミング言語 C、C++、Objective-C、Objective-C++ 向けのコンパイラフロントエンドという位置づけ。
・オフロード
    ハードウェアにCPUの処理を担ってもらうこと。
・リングバッファ
    キューが満タンになったときに最初に入力されたデータを上書きすることで、待ちやエラーをなくす。キュー構造を環状にした構造。
・kernel-devel
    カーネルソースの再構築時に必要なヘッダーファイルなどで構成されたパッケージ。
・kernel-headers
    他のプログラムから呼び出すことができるLinuxカーネルが提供する関数を含むファイル。
・inode番号
    ファイル・システム中の各ファイルは、そのファイル名に加えて、i ノード番号 と呼ばれる、ファイル・システムで固有の識別番号を持ってる。 i ノード番号は物理ファイル、すなわち特定のロケーションに保管されたデータを指しす。
・Chroot
    ルートファイルシステムを隔離する。
・Cgroup
    CPUやメモリなどのリソースの制限。
・ポーリング
    ホストコンピュータに複数の端末が接続されているネットワークシステムにおいて、端末に対して、送信したいデータがあるかどうかを問い合わせることである。 ポーリングは、一定間隔で各端末に送られ、端末からの送信要求に対して、送受信が行われる
・プロファイル
    プログラムの割り当てまたは処理にかかる時間、特定の命令の使用状況、または頻度を測定する動的プログラムを分析すること。
・
・
・
・
・
・


