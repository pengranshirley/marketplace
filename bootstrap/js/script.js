$(window).load(function() {
  $('#content').masonry({
   columnWidth: 360,
   itemSelector: '.picture'
  }).imagesLoaded(function() {
   $('#content').masonry('reload');
  });
});



