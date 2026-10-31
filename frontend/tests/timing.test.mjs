import test from 'node:test';
import assert from 'node:assert/strict';
import { secondsRemaining, deadlinePassed } from '../src/timing.ts';

test('critical: distraction 00:00 cannot become recall 00:00', () => {
  const now = 1800000150;
  const distractionDeadline = now;
  const recallDeadline = now + 120;
  assert.equal(secondsRemaining(distractionDeadline, 0, now), 0);
  assert.equal(secondsRemaining(recallDeadline, 0, now), 120);
  assert.equal(deadlinePassed(recallDeadline, 0, now), false);
});

test('recall remains available when only a fraction of a second has passed', () => {
  const deadline = 1800000270;
  assert.equal(secondsRemaining(deadline, 0, 1800000150.001), 120);
  assert.equal(deadlinePassed(deadline, 0, 1800000150.001), false);
});

test('server clock offset is applied to each new phase deadline', () => {
  const local = 1700000000;
  const serverOffset = 100000000;
  assert.equal(secondsRemaining(1800000120, serverOffset, local), 120);
  assert.equal(deadlinePassed(1800000120, serverOffset, local), false);
});

test('auto-submit is permitted only when the recall deadline is reached', () => {
  const deadline = 1800000270;
  assert.equal(deadlinePassed(deadline, 0, deadline - 0.001), false);
  assert.equal(secondsRemaining(deadline, 0, deadline - 0.001), 1);
  assert.equal(deadlinePassed(deadline, 0, deadline), true);
  assert.equal(secondsRemaining(deadline, 0, deadline), 0);
  assert.equal(deadlinePassed(deadline, 0, deadline + 30), true);
});

test('missing deadlines never authorize auto-submission', () => {
  assert.equal(secondsRemaining(null, 0, 1800000150), 0);
  assert.equal(deadlinePassed(null, 0, 1800000150), false);
});
