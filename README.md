# Lab List Maker

大学院ウェブサイトを根ノードとし（`depth = 0`）、「大学院 ➡︎ 研究科 ➡︎ 専攻分野 ➡︎ 研究室」の順に幅優先探索して、研究室のリストを作成します (`MAX_DEPTH = 3`)。ただし研究室は必ずしも左の組織構造を取りません。

また各研究室ウェブサイトから修士・博士課程の学生の名簿を探索します（開発中）。

## 準備

- 環境変数 `OPENAI_API_KEY`
- [uv](https://docs.astral.sh/uv/) 導入

## 実行

```sh
git clone git@github.com:pol-inc/lablist-maker.git
cd lablist-maker
uv sync
uv run src/make_lablist.py
# 開発中： uv run src/make_memberlist.py
```

ファイルが `output/(today)/` に出力されます。

追加作成したい大学院がある場合は `make_lablist.py` の `grads` を編集してください。

## コスト

使用モデルは `gpt-5-nano` です。2026-03 現在、OpenAI API からウェブ探索が利用できる最廉価モデルです（詳細：[OpenAI Model Pricing](https://developers.openai.com/api/docs/pricing)）

東京大学大学院に対し、`make_lablist.py` の消費トークンおよび料金例は以下の通りです（数値は変動します）。

### (memo)

個々のタスクは単純なので、ローカル言語モデル + [ddgs](https://github.com/deedy5/ddgs) でゼロコスト化してみたい。[Qwen 3.5 9B](https://huggingface.co/Qwen/Qwen3.5-9B) を検討中。

おそらく時間がかかるため、うまく分割処理したい。

### 補足：`while dq` は停止する

- `depth = 0` の `Node` で初期化
- `resp_text` は 0/1/2 で始まる
  - 0,1 のとき dq には追加しない
  - 2 のとき `new_node` は `node` より `depth` が 1 大きい
- `depth == NUM_INTERMEDIATE_LAYES` のとき `new_node` は append されない

➡︎ `while dq` は停止する。
