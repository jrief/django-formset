if (!('requestIdleCallback' in window) || !('cancelIdleCallback' in window)) {
	(window as any).requestIdleCallback = function (cb: any) {
		var start = Date.now();
		return setTimeout(function () {
			cb({
				didTimeout: false,
				timeRemaining: function () {
					return Math.max(0, 50 - (Date.now() - start));
				}
			});
		}, 1);
	};

	(window as any).cancelIdleCallback = function (id: any) {
		clearTimeout(id);
	};
}
