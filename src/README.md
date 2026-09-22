# Source

`model/` the completion network (`v5_model.py`), its sampler and channel assembly (`v5_data.py`), and the training loops for depth (`v5_train.py`) and for the shallowest-point hazard head (`train_hazard.py`).

`inference/` national inference (`national_v5.py`, optional test-time augmentation), ensembling (`ensemble_v6.py`), the distance blend with the nearest sounding (`blend_map.py`), the hazard field (`hazard_corridor.py`), and the standalone tool anyone can run on their own soundings (`seabednet_complete.py`).

`eval/` the tests. Each writes a JSON into `results/` and none of them grade on training data.

`data/` acquisition and preparation: NONNA fetch and tiling, the gravity prior, radar and imagery channels, survey-index dating for the temporal split, and the crowdsourced-bathymetry crawler.

`products/` what a planner would use: shoal lists, the danger-report model, survey plans, and the sealed forecast machinery.

`site/` builders for the public atlas and the technical report. They read the JSON in `results/` and never restate a number.
