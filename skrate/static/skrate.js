/* Event handling for buttons in Skrate skateboard progression app. */


function refresh_trick_element(trick_id) {
  // Call API to get updated html for a trick element (new stats)
  $.ajax({
    url: "/get_single_trick_stats/" + trick_id,
    success: function(response) {
      // Put the response data in appropriate element
      $("#trickstats" + trick_id).html(response);
    }
  });
}


function refresh_game_window() {
  // Call API to update the game status window after a turn in a game
  $.ajax({
    url: "/get_latest_game_view",
    success: function(response) {
      $("#outergame").html(response);
    }
  });
}


function record_attempt_and_update(element, is_successful) {
  // When button clicked for land or miss, make the call and update elements
  var trick_id = $(element).attr("id").split("-")[1];
  $.ajax({
    url: "/attempt/" + trick_id + "/" + is_successful.toString() + "/false",
    success: function(data) {
      // Update the trick element for new trick stats, at least
      refresh_trick_element(trick_id);
      // Check if the game element also needs to be updated, if so do it
      if (data.update_game) {
        refresh_game_window();
      }
    }
  });
}


$(".btn-trick-success").click(function() {
  console.log("Recording success...");
  record_attempt_and_update(this, true);
});


$(".btn-trick-miss").click(function() {
  console.log("Recording miss...");
  record_attempt_and_update(this, false);
});


$("#newgame").click(function() {
  console.log("Starting new game...");
  $.ajax({
    url: "/start_game",
    success: refresh_game_window
  });
});
