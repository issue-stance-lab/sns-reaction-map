import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.editorial_cycle import binding
from scripts.summarize_editorial_holds import summarize
from scripts.verify_editorial_hundred import dump


class CycleBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.run=Path(self.tmp.name)
        self.actor='/root/a';dump(self.run/'reservation.json',{'assignments':{'editor':{self.actor:[1]},'audit':{'/root/b':[1]}},'worktrees':{self.actor:str(Path.cwd()),'/root/b':'/some/other/worktree'}})

    def test_reject_unassigned_actor_before_creating_output(self):
        with self.assertRaises(ValueError):binding(self.run,1,'audit',self.actor)
        self.assertFalse((self.run/'batch-01').exists())

    def test_reject_wrong_worktree(self):
        with self.assertRaises(ValueError):binding(self.run,1,'audit','/root/b')
        self.assertFalse((self.run/'batch-01').exists())

    def test_binding_pins_reservation_and_never_rebinds(self):
        binding(self.run,1,'editor',self.actor)
        dump(self.run/'reservation.json',{'assignments':{'editor':{self.actor:[1]}},'worktrees':{self.actor:str(Path.cwd())},'changed':True})
        with self.assertRaises(ValueError):binding(self.run,1,'editor',self.actor)


class HoldSummaryTests(unittest.TestCase):
    def test_hint_is_not_adoption_and_missing_evidence_is_visible(self):
        row={'topic':'t','record_id_hash':'r','body_sha256':'b','classification_sha256':'c','adoption_status':'hold','reason_sha256':'x','first_route':'uncertain','proposed':{'stance':'yes'},'independent_proposed':{'stance':'no'}}
        before=row.copy();r=summarize([row],{'x':'引用の発言者が不明'})
        self.assertEqual(row,before);self.assertEqual(r['adoption_changes'],0)
        self.assertEqual(r['records'][0]['differing_fields'],['stance'])
        self.assertEqual(r['records'][0]['primary_reason_hint'],'quote_or_attribution')
        self.assertEqual(summarize([row],{})['records_with_unmapped_reason_evidence'],1)

    def test_only_holds_count(self):
        self.assertEqual(summarize([{'adoption_status':'accepted'}],{})['held_records'],0)


class OverlayTests(unittest.TestCase):
    def baseline(self):
        return {'batch':100007,'index':18,'topic':'t','record_id_hash':'id','body_sha256':'body','classification_sha256':'class','proposed':{'stance':'yes'},'current':{'stance':'yes'},'changes':{},'route':'retain_candidate','adoption_status':'pending_audit'}

    def test_overlay_preserves_original_and_requires_exact_old(self):
        from scripts.finalize_editorial_cycle import apply_overlay
        old=self.baseline();new={**old,'adoption_status':'accepted'}
        out=apply_overlay([old],{'overlay':[{'source_key':[old['batch'],old['index']],'old':old.copy(),'new':new}]})
        self.assertEqual(old['adoption_status'],'pending_audit');self.assertEqual(out,[new])
        with self.assertRaises(ValueError):apply_overlay([old],{'overlay':[{'source_key':[old['batch'],old['index']],'old':{**old,'body_sha256':'bad'},'new':new}]})

    def test_supplemental_reindex_or_reclassification_is_rejected(self):
        from scripts.finalize_editorial_cycle import apply_overlay
        old=self.baseline()
        for change in [{'index':0},{'proposed':{'stance':'no'}},{'body_sha256':'other'}]:
            with self.assertRaises(ValueError):apply_overlay([old],{'overlay':[{'source_key':[old['batch'],old['index']],'old':old,'new':{**old,'adoption_status':'accepted',**change}}]})

if __name__=='__main__':unittest.main()
