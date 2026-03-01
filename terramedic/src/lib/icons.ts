// Shared SVG path data for action icons (Heroicons outline, 24x24 viewBox)
export const ICON_PATHS = {
  clock: 'M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z',
  banknotes:
    'M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z',
  bolt: 'm3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z'
} as const;

export type IconName = keyof typeof ICON_PATHS;

// Green cross logo — two rect arms (viewBox "7 7 26 26" for cross-only)
export const GREEN_CROSS = {
	viewBox: '7 7 26 26',
	fill: '#2ecc71',
	arms: [
		{ x: 15, y: 7, width: 10, height: 26, rx: 1.5 },
		{ x: 7, y: 15, width: 26, height: 10, rx: 1.5 }
	]
} as const;
