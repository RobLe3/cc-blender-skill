"""Structural checks, not a substitute for native agent skill-loading evaluations."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import re
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(os.environ['CC_BLENDER_BASELINE']) if os.environ.get('CC_BLENDER_BASELINE') else None


class SkillContracts(unittest.TestCase):
    def test_manifest_and_frontmatter(self):
        manifest = json.loads((ROOT / 'plugin/manifest.json').read_text())
        self.assertEqual(manifest['version'], '1.4.0')
        self.assertEqual(len(manifest['skills']), 30)
        self.assertNotIn('claude-code', manifest['requires'])
        self.assertIn('agent-capabilities', manifest['requires'])
        self.assertIn('codex', manifest['clients'])
        self.assertIn('claude-code', manifest['clients'])
        names = set()
        for entry in manifest['skills']:
            path = ROOT / 'plugin' / entry['path']
            text = path.read_text()
            front, body = text.split('---', 2)[1:]
            name = re.search(r'^name: (.*)$', front, re.M).group(1)
            description = re.search(r'^description: (.*)$', front, re.M).group(1).strip('"\'')
            self.assertEqual(name, entry['name'])
            self.assertNotIn(name, names)
            names.add(name)
            self.assertLessEqual(len(description), 1024, name)
            self.assertNotRegex(front, r'^when_to_use:', name)
            allowed = set(re.search(r'^allowed-tools: (.*)$', front, re.M).group(1).split())
            used = set(re.findall(r'mcp__\w+__\w+', body))
            self.assertFalse(used - allowed, (name, used - allowed))
            if any(t.startswith('mcp__') for t in allowed):
                self.assertIn('mcp__blender__execute_blender_code', allowed)
                self.assertIn('mcp__blender_official__execute_blender_code', allowed)
            self.assertIn('mcp-backends.md', body)

    def test_all_python_parses(self):
        for p in (ROOT / 'plugin/skills').rglob('*.py'):
            ast.parse(p.read_text(), filename=str(p))

    def test_evals_and_baseline_preservation(self):
        files = list((ROOT / 'plugin/skills').rglob('evals.json'))
        total = 0
        for p in files:
            cases = json.loads(p.read_text())
            total += len(cases)
            self.assertTrue(all(isinstance(c['query'], str) and isinstance(c['should_trigger'], bool)
                                for c in cases))
            if BASELINE:
                old = json.loads((BASELINE / p.relative_to(ROOT)).read_text())
                self.assertTrue(all(case in cases for case in old))
        self.assertEqual(total, 225)
        scenarios = json.loads((ROOT / 'plugin/skills/text-to-blender/evals/backend-scenarios.json').read_text())
        self.assertEqual(len(scenarios), 10)
        self.assertEqual(len({c['id'] for c in scenarios}), len(scenarios))

    @unittest.skipUnless(BASELINE, 'Set CC_BLENDER_BASELINE to an extracted v1.3.0 tree')
    def test_original_recipe_blocks_unchanged(self):
        approved_changes = {
            ('blender-cameras', 5),   # Blender 5 layered Action F-curves
            ('blender-rendering', 2), # Version-guarded EEVEE settings
            ('blender-export', 1),    # Valid decimation API + context restoration
        }
        observed_changes = set()
        for old in (BASELINE / 'plugin/skills').glob('*/SKILL.md'):
            new = ROOT / old.relative_to(BASELINE)
            before = re.findall(r'```python\n(.*?)```', old.read_text(), re.S)
            after = re.findall(r'```python\n(.*?)```', new.read_text(), re.S)
            self.assertGreaterEqual(len(after), len(before), old.parent.name)
            for index, (old_block, new_block) in enumerate(zip(before, after)):
                key = (old.parent.name, index)
                if key in approved_changes:
                    self.assertNotEqual(old_block, new_block, key)
                    observed_changes.add(key)
                else:
                    self.assertEqual(old_block, new_block, key)
        self.assertEqual(observed_changes, approved_changes)
        for group in ['references', 'scripts', 'assets']:
            for old in (BASELINE / 'plugin/skills').glob('*/' + group + '/**/*'):
                if old.is_file():
                    self.assertEqual(old.read_bytes(), (ROOT / old.relative_to(BASELINE)).read_bytes(), str(old))

    def test_multires_api_layouts(self):
        path = ROOT / 'plugin/skills/blender-export/scripts/multires_bake_export.py'
        spec = importlib.util.spec_from_file_location('bake_layout', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modern = types.SimpleNamespace(bake=types.SimpleNamespace(use_multires=False))
        self.assertEqual(module.multires_bake_settings(modern)[1:],
                         ('use_multires', modern.bake, 'type'))
        legacy = types.SimpleNamespace(bake=types.SimpleNamespace(), use_bake_multires=False, bake_type='NORMALS')
        self.assertEqual(module.multires_bake_settings(legacy)[1:],
                         ('use_bake_multires', legacy, 'bake_type'))
        with self.assertRaises(RuntimeError):
            module.multires_bake_settings(types.SimpleNamespace(bake=types.SimpleNamespace()))


if __name__ == '__main__':
    unittest.main()
