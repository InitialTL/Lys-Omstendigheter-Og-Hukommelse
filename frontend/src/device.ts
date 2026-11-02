/** Device-specific *help text only*. This is never persisted or sent to the server.
 * Platform strings can be missing or spoofed, so core functionality stays device-agnostic.
 */
export type DeviceGuide = 'ios' | 'android' | 'windows' | 'macos' | 'linux' | 'generic';
export type DeviceSignals = {
  userAgent?: string;
  platform?: string;
  clientHintPlatform?: string;
  maxTouchPoints?: number;
};

export function detectDeviceGuide({ userAgent = '', platform = '', clientHintPlatform = '', maxTouchPoints = 0 }: DeviceSignals): DeviceGuide {
  const ua = userAgent.toLowerCase();
  const candidate = (clientHintPlatform || platform).toLowerCase();
  // iPadOS Safari can identify as MacIntel. Only use this for optional help.
  if (/ipad|iphone|ipod/.test(ua) || (candidate.includes('mac') && maxTouchPoints > 1)) return 'ios';
  if (ua.includes('android') || candidate.includes('android')) return 'android';
  if (candidate.includes('windows') || ua.includes('windows nt')) return 'windows';
  if (candidate.includes('mac') || /macintosh|mac os x/.test(ua)) return 'macos';
  if (candidate.includes('linux') || ua.includes('linux')) return 'linux';
  return 'generic';
}

export function currentDeviceGuide(): DeviceGuide {
  if (typeof navigator === 'undefined') return 'generic';
  const nav = navigator as Navigator & { userAgentData?: { platform?: string } };
  return detectDeviceGuide({
    userAgent: nav.userAgent,
    platform: nav.platform,
    clientHintPlatform: nav.userAgentData?.platform,
    maxTouchPoints: nav.maxTouchPoints,
  });
}
