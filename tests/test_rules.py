from services.file_order import numeric_file_key
from services.classifier import classify

def test_order():
    assert sorted(['Bitacoras 10.pdf','Bitacoras 2.pdf','Bitacoras 1.pdf'],key=numeric_file_key)==['Bitacoras 1.pdf','Bitacoras 2.pdf','Bitacoras 10.pdf']

def test_marep():
    assert classify('(M) WHEEL WORN',[])[0]=='MAREP'

def test_programado():
    assert classify('PERFORM TRANSIT CHECK',['TRANSIT CHECK'])[0]=='PROGRAMADO'
