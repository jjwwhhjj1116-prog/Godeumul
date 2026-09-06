import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from diorama_style_check import declaration, read_blocks, style_errors

class DioramaContractTest(unittest.TestCase):
    def test_paired_declaration(self):
        style=declaration()
        self.assertEqual(style_errors(style+' image',style+' motion'),[])
        self.assertTrue(style_errors(style+' image','realistic portrait'))

    def test_blocks_and_bad_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'batch.txt'
            p.write_text('First scene.\n\nSecond scene.\n',encoding='utf-8-sig')
            self.assertEqual(len(read_blocks(p)),2)
            for bad in ['', 'Same\n\nSame', 'A\n\n\nB', 'Scene 1: A', '한글', 'A\nB']:
                p.write_text(bad,encoding='utf-8-sig')
                with self.subTest(bad=bad),self.assertRaises(ValueError):
                    read_blocks(p)

if __name__=='__main__':
    unittest.main()
