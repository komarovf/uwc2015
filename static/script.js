//Hoping that server TCP conn timeout is greater than time for generating sitemap :O
$(document).ready(function() {
	$('#start').click(function() {
		var url = $('#url').val();

		$('#start').attr('disabled', true);
		$('#start').text('Processing..');
		$('#result, #errors, #warnings').empty();

		$.post('/generate_sitemap', {
			url: url
		}).done(function(result) {
			//Display results from server
			$('#start').attr('disabled', false);
			$('#start').text('Get sitemap.xml');

			if (result.data) {
				$('#result').html('<p><a href="'+result.data+'">sitemap.xml for '+url+'</a></p>');
				if (result.warnings) {
					var warn = '';
					for (var i=0; i<result.warnings.length; i++) {
						warn += '<p>' + result.warnings[i] + '</p>';
					}
					$('#warnings').html(warn);
				}
			} else {
				$('#errors').html('<p>'+result.errors[0]+'</p>');
			}
		}).fail(function() {
			$('#start').attr('disabled', false);
			$('#start').text('Get sitemap.xml');
			$('#errors').html('<p>Something went wrong.. Try again later.</p>');
		});
	});
})