def web_page(AcX, AcY, AcZ):

    html_page = """
<!DOCTYPE html>
<html>
  <head>
    <style>
        .slidecontainer {
          width: 100%;
        }
        
        .slider {
          -webkit-appearance: none;
          width: 100%;
          height: 25px;
          background: #d3d3d3;
          outline: none;
          opacity: 0.7;
          -webkit-transition: .2s;
          transition: opacity .2s;
        }
        
        .slider:hover {
          opacity: 1;
        }
        
        .slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 25px;
          height: 25px;
          background: #04AA6D;
          cursor: pointer;
        }
        
        .slider::-moz-range-thumb {
          width: 25px;
          height: 25px;
          background: #04AA6D;
          cursor: pointer;
        }
    </style>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <script>
      var ajaxRequest = new XMLHttpRequest();

      function ajaxLoad(ajaxURL) {
        ajaxRequest.open("GET", ajaxURL, true);
        ajaxRequest.onreadystatechange = function () {
          if (ajaxRequest.readyState == 4 && ajaxRequest.status == 200) {
            var ajaxResult = ajaxRequest.responseText;
            var array = ajaxResult.split("|");
            document.getElementById("AcX").innerHTML = array[0];
            document.getElementById("AcY").innerHTML = array[1];
          }
        };
        ajaxRequest.send();
      }

      function updateDHT() {
        ajaxLoad("getDHT");
      }

      setInterval(updateDHT, 1000);

    </script>

    <title>SenseU</title>
  </head>

  <body>
    <center>
      <div id="main">
        <h1>SenseU</h1>
        <h4>Web server on ESP32</h4>
        <div id="content">
            <form id="Adjust_form">
          <p>
            Horizontal Movement: <strong><span id="AcX">--.-</span></strong>
          </p>
          <div class="slidecontainer">
            <input type="range" name="AcX_slider" min="1" max="1000" value='""" + str(AcX) + """' class="slider" id="AcX">
            <p>Value: <span id="AcX_value"></span></p>
            </p>
          </div>

          <p>
            Vertical Movement: <strong><span id="AcY">--.-</span></strong>
          </p>
          <div class="slidecontainer">
            <input type="range" name="AcY_slider" min="1" max="1000" value='""" + str(AcY) + """' class="slider" id="AcY">
            <p>Value: <span id="AcY_value"></span></p>
            </p>
          </div>

          <p>
            Side-to-Side Movement: <strong><span id="AcZ">--.-</span></strong>
          </p>
          <div class="slidecontainer">
            <input type="range" name="AcZ_slider" min="1" max="1000" value='""" + str(AcZ) + """' class="slider" id="AcZ">
            <p>Value: <span id="AcZ_value"></span></p>
            </p>
          </div>

          <p>
            Horizontal Position: <strong><span id="GyX">--.-</span></strong>
          </p>
          <p>
            Vertical Position: <strong><span id="GyY">--.-</span></strong>
          </p>
          <p>
            Side-to-Side Position: <strong><span id="GyZ">--.-</span></strong>
          </p>
        </div>

        <script>
        
            document.getElementById("AcX_value").innerHTML = document.getElementById("AcX").value;
            document.getElementById("AcX").oninput = function() {
                document.getElementById("AcX_value").innerHTML = this.value;
            }
            document.getElementById("AcX").onmouseup = function() {
              document.getElementById("Adjust_form").submit();
            }

            document.getElementById("AcY_value").innerHTML = document.getElementById("AcY").value;
            document.getElementById("AcY").oninput = function() {
                document.getElementById("AcY_value").innerHTML = this.value;
            }
            document.getElementById("AcY").onmouseup = function() {
              document.getElementById("Adjust_form").submit();
            }
            </script>
      </div>
    </center>
  </body>
</html>





    """
    return html_page