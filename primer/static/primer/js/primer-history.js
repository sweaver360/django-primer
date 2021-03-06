!function() {

	var prevPath = null;
	var hasHistorySupport = !!(window.history && history.pushState);

	/**
	 * Constructor
	 */
	function __init__() {

		prevPath = window.location.pathname;
		$(document).on('click.history', 'a[data-ajax]', handleAjaxLinks);
		$(window).on('popstate', onStateChange);
	}


	/**
	 * Handles links for the data-ajax api
	 */
	function handleAjaxLinks(e) {
		e.preventDefault();
		var anchor = $(this);
		var options = {
			url : anchor.attr('href'),
			layout: anchor.data('ajax'),
		}

		if (anchor.data('target')) options['container'] = anchor.data('target');

		pushState(options);
	}


	/**
	 * Triggered from a pop state event
	 */
	function onStateChange(e) {
		var state = history.state;
		var url = window.location.pathname + window.location.search + window.location.hash;
		var title = document.title;
		
		if (state && 'container' in state) {
			var container = $(state.container);
		} else {
			var container = $('#body');
		}

		
		// check to see that our path actually changed. This means a real page load
		// and not just a hash that is getting added
		if (prevPath.split('#')[0] != url.split('#')[0]) {

			$(window).trigger('beforePageLoad');
			
			// the actual page loading handler
			$.get(url, { layout: state.layout }, function(data){
				container.html(data);

				if (state.scroll || (state.layout == 'app' || !state.layout)) $(window).scrollTop(0);
				
				var namespace = $('#primer-css-namespace').remove().val();
				if (namespace) {
					var htmlEl = $('html');
					htmlEl.removeClass(htmlEl.data('cssnamespace'));	
					htmlEl.addClass(namespace);
					htmlEl.data('cssnamespace', namespace);
				}
				
				
				//lets page anchors jump to where they are supposed to
				if (window.location.hash) window.location.hash = window.location.hash
				$(window).trigger('pageLoaded');
			});
		} else if (url.split('#').length > 1) {
			setTimeout(function(){
				window.location.hash = window.location.hash
			}, 1);
			
		}

		prevPath = url;
	}

	
	/**
	 * Core page handler
	 */
	function pushState(options, callback){

		var defaults = {
			url : null,
			container : null,
			data : {},
			title : document.title,
			layout : null,
			callback : $.noop,
			scroll : false
		}

		//handle optionally passing load page just a url
		if (typeof(options) == 'string') {
			var config = $.extend({}, defaults, {url: options, callback: callback || $.noop});
		} else {
			var config = $.extend({}, defaults, options);
		}

		//return if we dont have a url
		if (!config.url) return;

		//handle callbacks from loadPage
		$(window).one('pageLoaded', config.callback);

		//if we have history support, we can use pushstate,
		//otherwise we will just redirect
		if (hasHistorySupport) {
			
			config.data['layout'] = config.layout;

			if (!config.container) {
				if (config.layout == 'app') {
					config.container = '#main';
				} else {
					config.container = '#body';
				}	
			}

			//set data for for pushState
			config.data['container'] = $(config.container).selector;
			config.data['layout'] = config.layout;
			config.data['scroll'] = config.scroll;

			history.pushState(config.data, config.title, config.url);
			$(window).trigger('popstate');

		} else {
			window.location = config.url;
		}
		
	};


	/***********************************************************************************
	 * Public API via jQuery
	 ***********************************************************************************/ 
	$.pushState = pushState;

	//init on dom ready
	$(__init__);

}(jQuery);