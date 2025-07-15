## 詳細な README

[![en](https://img.shields.io/badge/lang-en-blue.svg)](https://github.com/santec-corporation/Python-IL-STS/blob/main/docs/README.md)

> [!IMPORTANT]    
> ⚠️ 実行前に必ず確認してください。
> スクリプトを実行する前の注意事項
>  -  TSL LDダイオードがオンになっていることを確認し、30分間ウォームアップしてください。
>  -  STS操作を実行する前に、MPMのゼロ調整を行うことをお勧めします。


## コアスクリプトの概要
- [get_address.py](/./src/santec/get_address.py): GPIBおよびUSBを介して接続された機器を検出します。
- [tsl_instrument_class.py](/./src/santec/tsl_instrument_class.py): TSL機器機能を管理します。
- [mpm_instrument_class.py](/./src/santec/mpm_instrument_class.py): MPM機器操作を処理します。
- [daq_device_class.py](/./src/santec/daq_device_class.py):DAQデバイスと対話します。
- [sts_process.py](/./src/santec/sts_process.py): 掃引されたテストシステムからのデータを処理します。
- [error_handling_class.py](/./src/santec/error_handling_class.py): 機器DLLおよびSTSプロセスDLLに関連するエラーを管理します。
- [file_saving.py](/./src/santec/file_saving.py): スイープテストシステムの運用データを記録します。

---

## LAN構成

#### 1。`main.py`ファイルを開きます。

#### 2。 `connection()`関数の以下のコードを交換します。

```python
def connection():
    tsl: TslInstrument
    mpm: MpmInstrument
    daq: SpuDevice
    
    device_address = GetAddress()
    device_address.initialize_instruments(is_tsl_mpm=False)

    tsl = TslInstrument(interface="LAN", ip_address="192.168.1.161") # TSLのIPアドレスに置き換えてください
    tsl.connect()

    mpm = MpmInstrument(interface="LAN", ip_address="192.168.1.162")  # MPMのIPアドレスに置き換えてください
    mpm.connect()
    
    if "220" in mpm.idn():
        return tsl, mpm, None

    daq_address = device_address.get_daq_address()
    daq = SpuDevice(device_name=daq_address)
    daq.connect()

    return tsl, mpm, daq
```

#### 3. ここからの手順に従ってください [システムの初期化](https://github.com/santec-corporation/Santec_IL_STS/blob/main/docs/README.jp.md#1-initialize-the-system).


---

## スクリプトの実行方法

スクリプトを実行する前に、機器接続を確認します, <br>
- [フロント接続](https://github.com/santec-corporation/Santec_IL_STS/blob/stable/docs/connection_front.png)
- [リア接続](https://github.com/santec-corporation/Santec_IL_STS/blob/stable/docs/connection_rear.png)

#### 1。システムを初期化します
`main.py`スクリプトを実行して、測定インターフェイスを起動します。

#### 2。機器の選択
以下を選択してください。\
光源、\
パワーメーター、\
DAQボード。

#### 3。参照データ構成
- プログラムは、以前に保存された参照データを検索します。
- データが見つからない場合は、次のスイープパラメーターを入力します。
波長を開始して停止します、\
スイープスピード、\
スイープ解像度（ステップサイズ）、\
出力電力、\
測定するMPM光学チャネル、\
光学的範囲。

#### 4。既存のデータの利用
記録された参照データが利用可能な場合、スクリプトはスイープパラメーターと関連するデータをアップロードするように求められます。

#### 5。光チャネル接続
- プロンプトに従って、選択した各光学チャネルを接続します。
- 参照データの測定を開始します。

**注**：パッチコードを使用して、TSLを各光ポートに直接接続します。

#### 6。テスト中のデバイスを接続する（DUT）
-  DUTを接続します。
- 測定繰り返しの数を入力します。
-  Enterを押して測定を開始してください。

#### 7。測定結果
- スクリプトに挿入損失の結果が表示されます。
- 必要に応じて2回目の測定を行うことも可能です。
- それ以上の測定が不要な場合、スクリプトは参照データとDUTデータを保存します。
- 楽器は自動的に切断されます。

---

## スイープ構成パラメーター

**ファイルタイプ** [JSON](https://www.json.org/json-ja.html) <br>
**ファイル名** **last_scan_params.json**

### 例
  ```json
  {
      "selected_chans": [
          ["0", "1"],
          ["0", "2"]
      ],
      "selected_ranges": [
          1,
          2
      ],
      "start_wavelength": 1500.0,
      "stop_wavelength": 1600.0,
      "sweep_step": 0.1,
      "sweep_speed": 50.0,
      "power": 0.0,
      "actual_step": 0.1
  }
  ```

### カスタマイズのヒント

**チャネル選択**<br>
**selected_chans** アレイを調整して、分析に必要なチャネルを含めます。
各組み合わせを使用すると、異なる構成を比較できます。

**範囲の選択**<br>
実験設計に応じて、**selected_ranges** を変更して特定の範囲を選択します。
インデックスが利用可能な範囲オプションに一致するようにします。

**波長設定**<br>
**start_wavelength** と **stop_wavelength** を変更して、測定の対象のスペクトル範囲を定義します。

**スイープパラメーター**<br>

**ステップサイズ**<br>
より細かいまたは粗いサンプリングのために **sweep_step** を調整してください。ステップサイズを小さくすると、より詳細なデータが得られます。

**速度**<br>
必要な精度と結果に応じて、結果が必要な速さに基づいて **sweep_speed** を調整します。

**電源調整**<br>
測定中に機器の要件と望ましい感度に基づいて電力パラメーターを設定します。

**実際のステップ**<br>
2つのTSLトリガーの間のステップサイズ。この値は、TSLスイープパラメーターを設定した後に取得されます。`tsl_instrument_class`の`set_sweep_parameters`を参照してください。

---

## Santecがテストシステムを席巻したことについて

### STS IL PDLとは何ですか？
スイープテストシステムは、Santec Corporationが提供するフォトニックソリューションです。
受動的光学デバイスの波長依存性損失特性評価を実行します。
構成は以下の通りです。
- **光源** TSLとしても知られるSANTECの調整可能な半導体レーザー
- **パワーメーター** MPMとも呼ばれるSantecのマルチポートパワーメーター

### スイープテストシステムの詳細については [ここをクリック](https://inst.santec.com/jp/products/componenttesting/sts)