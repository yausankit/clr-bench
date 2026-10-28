# Input files edited for release

The files below were edited after the chains were built, only to replace local proxy addresses and
host names with environment variables or neutral wording. No data or logic changed. Their original SHA-256 is
listed; where a chain manifest records the file, `tools/rebuild_chain.sh` skips it in the input check.

| File | Original SHA-256 | In manifests of |
|---|---|---|
| `inputs/CH/build_salience.py` | `a61a33698f7718bab691877d633a898515a433f4bd4fd853bc58744a5bb80ae5` | CH1 CH2 |
| `inputs/CH/sources/FETCH.md` | `df341733e1c8f6a246df0101f2ad3067a2cd180515c469bb8078bcdf2a56d32b` | CH1 CH2 |
| `inputs/LG/sources/FETCH.md` | `912996396981ed0ad993de55992777132084c4b382dcc33cb2278aac419e0ed1` | LG1 LG2 |
| `inputs/MN/sources/FETCH.md` | `3c7da652fb54f2827bdf45b10f49d1d21a3d2cbf5f04519daac1978965fdea31` | MN1 |
| `inputs/SP/build_inputs.py` | `7e6b6a9623df878924fb9043d06611d2f252133408739950faab1f392d51f52a` | SP1 SP2 |
| `inputs/SP/sources/FETCH.md` | `92197ca18dc8a6c727d7d6b00ad209011650bf8df2e0e7e06fe3691c16c6f05a` | SP1 SP2 |
| `inputs/SY/sources/FETCH.md` | `0ebfbae9fb40819f15882bd08b29a291251cef0dc256103199261a953fec8435` | SY1 SY2 |
| `inputs/TR/fetch_currency_pageviews.py` | `17c091d8ce116358c2917bbcc92422602d8f40475e9f1a2b89f2608f9328ac7b` | TR1 TR2 |
| `inputs/TR/fetch_currency_wiki.py` | `fe1c37f12730da6b35da0375ff60abc360e6b0054d92c7319fc14c6294325e2f` | TR1 TR2 |
| `inputs/UN/fetch_salience.py` | `e1dbc2ade06ba16b2ba0b1f20655db403469ccf10b6d805760eb15932f8be6df` | UN1 UN2 |
| `inputs_alt/MN/sources/FETCH.md` | `3e4adc329533c41c899283b14225eb10d1c7d2cfb3f309bcddfe145e90cba1bc` | MN2 |
| `inputs_alt/UN/fetch_salience.py` | `e1dbc2ade06ba16b2ba0b1f20655db403469ccf10b6d805760eb15932f8be6df` | UN1 UN2 |
