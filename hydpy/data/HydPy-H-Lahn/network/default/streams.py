from hydpy import Node, Element


Element("stream_dill_assl_lahn_leun", inlets="dill_assl", outlets="lahn_leun", keywords=["river"])

Element("stream_lahn_marb_lahn_leun", inlets="lahn_marb", outlets="lahn_leun", keywords=["river"])

Element("stream_lahn_leun_lahn_kalk", inlets="lahn_leun", outlets="lahn_kalk", keywords=["river"])
