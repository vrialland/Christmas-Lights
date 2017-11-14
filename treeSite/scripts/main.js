$(document).ready(function(){
	$(".artBtn").click(function()
	{
		sendMsg($(this).attr("value"))
	});

	sendMsg = function(msg) {
		var connection = new WebSocket('ws://192.168.1.35:12000');

		connection.onopen = function () {
			connection.send(msg);
		};
	}
})