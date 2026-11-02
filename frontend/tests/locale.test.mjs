import test from 'node:test';
import assert from 'node:assert/strict';
import { detectBrowserLanguage, directionForLanguage, translate, hasInterfaceTranslation, LANGUAGE_NAMES, OS_HELP } from '../src/i18n.ts';
import { interfaceKeys } from '../src/localeKeys.ts';

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

test('every displayed interface message is translated in every listed language', () => {
  assert.equal(interfaceKeys.length, 164);
  for (const code of Object.keys(LANGUAGE_NAMES)) {
    for (const key of interfaceKeys) {
      assert.ok(hasInterfaceTranslation(code, key), `Missing ${code}: ${key}`);
      assert.ok(translate(key, key, code).trim(), `Blank ${code}: ${key}`);
    }
    for (const platform of Object.keys(OS_HELP)) {
      assert.ok(OS_HELP[platform][code], `Missing ${code} device guide: ${platform}`);
    }
  }
});

test('Dutch and all other additional study languages have actual interface translations', () => {
  assert.equal(translate('', 'Withdraw consent', 'nl'), 'Toestemming intrekken');
  assert.equal(translate('', 'Can the colors around us', 'nl'), 'Kunnen de kleuren om ons heen');
  assert.equal(translate('', 'Sit in a completely dark room', 'nl'), 'Zorg dat je in een volledig donkere kamer zit');
  for (const lang of ['nl','it','pt','da','pl','ro']) {
    for (const key of ['Withdraw consent','See my results','Submit answers','Sit in a completely dark room',
      'The study is complete','Share the link','Time remaining']) {
      assert.notEqual(translate('', key, lang), key, `English fallback for ${lang}: ${key}`);
    }
  }
});
