import test from 'node:test';
import assert from 'node:assert/strict';
import {detectDeviceGuide} from '../src/device.ts';

test('mobile browser guidance uses iOS and Android instead of defaulting to Windows', () => {
  assert.equal(detectDeviceGuide({userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X)',platform:'iPhone'}), 'ios');
  assert.equal(detectDeviceGuide({userAgent: 'Mozilla/5.0 (Linux; Android 14; Pixel 8)',platform:'Linux armv8l'}), 'android');
  assert.equal(detectDeviceGuide({userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',platform:'MacIntel',maxTouchPoints:5}), 'ios');
});

test('desktop and unknown device guidance stays optional', () => {
  assert.equal(detectDeviceGuide({userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',platform:'Win32'}), 'windows');
  assert.equal(detectDeviceGuide({platform:'MacIntel',maxTouchPoints:0}), 'macos');
  assert.equal(detectDeviceGuide({userAgent:'Mozilla/5.0 (X11; Linux x86_64)'}), 'linux');
  assert.equal(detectDeviceGuide({}), 'generic');
});

test('browser platform hints provide a fallback, but never require OS input', () => {
  assert.equal(detectDeviceGuide({clientHintPlatform:'Android',userAgent:''}), 'android');
  assert.equal(detectDeviceGuide({clientHintPlatform:'Windows',userAgent:''}), 'windows');
});
