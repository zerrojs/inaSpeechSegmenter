#!/usr/bin/env python
# encoding: utf-8

# The MIT License

# Copyright (c) 2018 Ina (David Doukhan - http://www.ina.fr/)

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import unittest
import os
import warnings
from inaSpeechSegmenter import Segmenter
from inaSpeechSegmenter.segmenter import _wav2feats
import filecmp
import pandas as pd
import numpy as np
import tempfile

class TestInaSpeechSegmenter(unittest.TestCase):
    
    def test_init(self):
        seg = Segmenter()

    def test_execution(self):
        # if this test fails, then you should check to correctness of your
        # tensorflow installation
        seg = Segmenter()
        ret = seg('./media/musanmix.mp3')

    def test_silence_features(self):
        # test empty signal do not result in warnings
        with warnings.catch_warnings(record=True) as w:
            ret = _wav2feats('./media/silence2sec.wav')
            assert len(w) == 0, [str(e) for e in w]

        
    def test_short(self):
        seg = Segmenter(vad_engine='sm')
        ret = seg('./media/0021.mp3')
        ref = [('male', 0, 0.66)]
        self.assertEqual(ref, ret)

    def test_boundaries(self):

        def seg2str(iseg, tseg):
            label, start, stop  = tseg
            return 'seg %d <%s, %f, %f>' % (iseg, label, start, stop)
        
        seg = Segmenter()
        ret = seg('./media/musanmix.mp3')
        for i in range(len(ret) -1):
            curstop = ret[i][2]
            nextstart = ret[i+1][1]
            self.assertEqual(curstop, nextstart,
                             '%s VS %s' % (seg2str(i, ret[i]), seg2str(i+1, ret[i+1])))

    def test_processingresult(self):
        seg = Segmenter(vad_engine='sm')
        ret = seg('./media/musanmix.mp3')
        df = pd.read_csv('./media/musanmix-sm-gender.csv', sep='\t')
        ref = [(l.labels, float(l.start), float(l.stop)) for _, l in df.iterrows()]
        self.assertEqual([e[0] for e in ref], [e[0] for e in ret])
        np.testing.assert_almost_equal([e[1] for e in ref], [e[1] for e in ret])
        np.testing.assert_almost_equal([e[2] for e in ref], [e[2] for e in ret])
        
    def test_batch(self):
        seg = Segmenter(vad_engine='sm')
        with tempfile.TemporaryDirectory() as tmpdirname:
            lout = [os.path.join(tmpdirname, '1.csv'), os.path.join(tmpdirname, '2.csv')]
            ret = seg.batch_process(['./media/musanmix.mp3', './media/musanmix.mp3'], lout)
            self.assertTrue(filecmp.cmp(lout[0], lout[1]))
            self.assertTrue(filecmp.cmp(lout[0], './media/musanmix-sm-gender.csv'))

    def test_program(self):
        ret = os.system('CUDA_VISIBLE_DEVICES="" ./scripts/ina_speech_segmenter.py -i ./media/0021.mp3 -o ./')
        self.assertEqual(ret, 0, 'ina_speech_segmenter returned error code %d' % ret)

    def test_startsec(self):
        # test start_sec argument
        seg = Segmenter()
        start_sec = 2.
        for lab, start, stop in seg('./media/musanmix.mp3', start_sec=start_sec):
            self.assertGreaterEqual(start, start_sec)
            self.assertGreaterEqual(stop, start_sec)

    def test_stopsec(self):
        # test stop_sec argument
        seg = Segmenter()
        stop_sec = 5.
        for lab, start, stop in seg('./media/musanmix.mp3', stop_sec=stop_sec):
            self.assertLessEqual(stop, stop_sec)
            self.assertLessEqual(start, stop_sec)
        
if __name__ == '__main__':
    unittest.main()
