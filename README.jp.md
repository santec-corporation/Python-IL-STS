
<p align="right"> <a href="https://www.santec.com/jp/" target="_blank" rel="noreferrer"> <img src="https://www.santec.com/dcms_media/image/common_logo01.png" alt="santec" 
  width="250" height="45"/> </a> </p>

<h1 align="left"> Santec IL STS </h1>

挿入損失（IL）を測定するためのプログラムです。 <br> <br>

[![en](https://img.shields.io/badge/lang-en-blue.svg)](https://github.com/santec-corporation/Python-IL-STS/blob/main/README.md)

## 概要

**SANTEC_IL_STS** は、SANTECスイープテストシステム（STS）の構成および操作を行うために設計されています。<br>
このツールは、SANTECのTSLおよびMPMシリーズ機器を使用して、挿入損失（IL）の測定を容易にします。

---

## 重要な機能

- 各機器を構成します（光源：TSLシリーズ、パワーメーター：MPMシリーズ、DAQボード）
- 波長スキャンの実行
- 参照スキャンパワーおよび測定スキャンの記録
- 挿入損失（IL）データの計算と保存
- 過去のスキャンパラメーターおよび参照データの再利用

---

## はじめる

### システム要件

**Python**（推奨バージョン：3.12）をインストールしてください。

**プラットフォーム** Windows 10
- **ドライバー** 
  - NI-488.2: [バージョン 20](https://www.ni.com/en/support/downloads/drivers/download.ni-488-2.html#345631)
  - NI-DAQmx: [バージョン 20](https://www.ni.com/en/support/downloads/drivers/download.ni-daq-mx.html#346240)
  - NI-VISA: [バージョン 20](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html#346210)

**プラットフォーム** Windows 11
- **ドライバー** 
  - NI-488.2: [バージョン 2024 Q3](https://www.ni.com/en/support/downloads/drivers/download.ni-488-2.html#544048) (Latest)
  - NI-DAQmx: [バージョン 2024 Q4](https://www.ni.com/en/support/downloads/drivers/download.ni-daq-mx.html#549669) (Latest)
  - NI-VISA: [バージョン 2024 Q4](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html#548367) (Latest)

### 依存関係

- [pythonnet](https://pythonnet.github.io/) : .NETの相互運用性については、`clr`とも呼ばれます
- [pyvisa](https://pyvisa.readthedocs.io/en/latest/index.html) : 測定デバイスの制御用
- [nidaqmx](https://nidaqmx-python.readthedocs.io/en/latest/) : NIDAQドライバーインタラクションのAPI
- Santec DLLs: _Instrument DLL_, _STSProcess DLL_ and _FTD2XX_NET DLL_.
  <br>
  こちらのDLLドキュメントを参照してください。<br>
  [DLLについて](https://github.com/santec-corporation/Python-IL-STS/blob/stable/src/santec/DLL/README.jp.md)

### サポートされている機器
掃引テストシステムである **IL PDL** ソフトウェアは、以下の機器と連携するように設計されています。
- _TSL-510, TSL-550, TSL-570, TSL-710 and TSL-770 レーザーシリーズ_
- _MPM-210 and MPM210H パワーメーターシリーズ_

### サポートされている機器接続
- **TSL-510, TSL-550, TSL-710**  
  **サポートされているインターフェイス** GPIB

- **TSL-570, TSL-770**  
  **サポートされているインターフェイス** GPIB, USB, or LAN

- **MPM-210H**  
  **サポートされているインターフェイス** GPIB, USB, or LAN

---

## インストールと実行

### Pythonインストール

**Python のダウンロードとインストール**
バージョン3.12が推奨されます。
- [python ダウンロード](https://www.python.org/downloads/)ページに移動します。
- 最新バージョンをダウンロードします。
- オペレーティングシステムのインストール手順に従ってください。

### リポジトリのクローニング

リポジトリをクローンするには、端末で次のコマンドを使用します。

```bash
git clone https://github.com/santec-corporation/Santec_IL_STS.git
```

### 最新リリースのダウンロード
[リリース](https://github.com/santec-corporation/santec_il_sts/releases)ページから最新リリースを直接ダウンロードできます。

### プログラムの実行
1. プロジェクトディレクトリに移動し、
   ```bash
    cd Santec_IL_STS
   ```
   
2. 依存関係をインストールし、
   ```bash
    pip install -r docs/requirements.txt
   ```

3. プログラムを実行し、
   ```bash
    python main.py
   ```

（オプション）追加の手順

4. ロギングを有効にし、ファイルにログを記録します。
   ```bash
    python main.py --enable_logging=True
   ```

5. ログを画面に出力するには、`main.py` 内の `log_to_screen()` メソッドを呼び出してください。

### 依存ライブラリのアップグレード

- **Pythonnetのアップグレード**
  ```bash
  pip install --upgrade pythonnet
  ```

- **Pyvisaのアップグレード**
  ```bash
  pip install --upgrade pyvisa
  ```
  
- **nidaqmxをアップグレードします**
  ```bash
  pip install --upgrade nidaqmx
  ```

<br/>

### プロジェクトの詳細については、こちらの README をご覧ください。[ここでお願いします](https://github.com/santec-corporation/Santec_IL_STS/blob/stable/docs/README.jp.md).
