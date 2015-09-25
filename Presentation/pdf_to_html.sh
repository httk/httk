#!/bin/bash

cat > httk_overview.html <<EOF
  <div style="margin: 0 auto;"><div style="display:inline-block;vertical-align:middle;"><span style="font-size: 300%;"><a href="#" onclick="return false;" class="unslider-arrow prev" style="text-decoration:none;">&lt;</a>&nbsp;&nbsp;</span>
  </div>
  <div style="display:inline-block; vertical-align:middle; width: 35em; height: 26.25em; overflow: hidden; border-style: solid; border-width: 3;">
  <script src="_static/unslider.min.js"></script>
  <style>
  .banner { position: relative; overflow: auto; padding:0; margin:0; }
    .banner li { list-style: none; vertical-align: middle; }
        .banner ul li { float: left; padding: 0; margin: 0;}
        .banner img {vertical-align: middle; width: 100%; }
  </style>
  <script>
  \$(window).load(function() {
    var unslider = \$('.banner').unslider({
	speed: 500,               //  The speed to animate each slide (in milliseconds)
	delay: false,              //  The delay between slide animations (in milliseconds)
	complete: function() {},  //  A function that gets called after every slide animation
	keys: true,               //  Enable keyboard (left, right) arrow shortcuts
	dots: false,               //  Display dot navigation
	fluid: false              //  Support responsive design. May break non-responsive designs
   });
    
    \$('.unslider-arrow').click(function() {
        var fn = this.className.split(' ')[1];
        unslider.data('unslider')[fn]();
    });
  });
  </script>
  <div class="banner">
    <ul style="margin:0; padding:0">
EOF

mkdir -p images
cd images
rm -f httk_overview_img_*.png 
convert -density 135 ../presentation.pdf httk_overview_img_%02d.png
ls *.png | sort -n | (
    while read LINE; do
        echo "<li><img src=\"_static/httk_overview/$LINE\" /></li>" >> ../httk_overview.html
    done
)

cat >> ../httk_overview.html <<EOF
    </ul>
  </div>
  <!--center>
  <span style="font-size: 300%;"><a href="#" onclick="return false;" class="unslider-arrow prev"> &lt;</a>&nbsp;&nbsp;
  <a href="#" onclick="return false;" class="unslider-arrow next"> &gt;</a></span>
  </center-->
  </div>
  <div style="display:inline-block;vertical-align:middle;">
  <span style="font-size: 300%;">&nbsp;&nbsp;<a href="#" onclick="return false;" class="unslider-arrow next" style="text-decoration:none;">&gt;</a></span>
  </div>
  <p><a href="_static/httk_overview.pdf">Download this presentation as a pdf.</a></p>
  </div>
EOF
