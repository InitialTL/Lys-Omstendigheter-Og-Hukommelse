import test from 'node:test';
import assert from 'node:assert/strict';
import { detectBrowserLanguage, directionForLanguage, translate, LANGUAGE_NAMES, OS_HELP } from '../src/i18n.ts';

test('browser language chooses a supported locale without silently assuming Norwegian', () => {
  assert.equal(detectBrowserLanguage(['pt-BR','fr-FR']), 'pt');
  assert.equal(detectBrowserLanguage(['no-NO']), 'nb');
  assert.equal(detectBrowserLanguage(['nn-NO']), 'nb');
  assert.equal(detectBrowserLanguage(['es-MX']), 'es');
  assert.equal(detectBrowserLanguage(['ja-JP']), 'en');
  assert.equal(detectBrowserLanguage([]), 'en');
});

test('RTL direction is available for future vetted language packs', () => {
  for (const code of ['ar','he','fa-IR','ur-PK']) assert.equal(directionForLanguage(code),'rtl');
  for (const code of ['en','nb','de','fr','ja']) assert.equal(directionForLanguage(code),'ltr');
});

test('all scored languages have a translation fallback and brightness directions', () => {
  for (const code of Object.keys(LANGUAGE_NAMES)) {
    assert.ok(translate('Tid igjen','Time remaining',code));
    for (const platform of Object.keys(OS_HELP)) assert.ok(OS_HELP[platform][code] ?? OS_HELP[platform].en);
  }
});
