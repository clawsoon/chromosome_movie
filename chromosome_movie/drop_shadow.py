filter = '''
  <defs>
    <filter style="color-interpolation-filters:sRGB;" id="dropshadow">
      <feFlood
         flood-opacity="0.5"
         flood-color="rgb(0,0,0)"
         result="flood" />
      <feComposite
         in="flood"
         in2="SourceGraphic"
         operator="in"
         result="composite1" />
      <feGaussianBlur
         in="composite1"
         stdDeviation="3"
         result="blur" />
      <feComposite
         in="SourceGraphic"
         in2="offset"
         operator="over"
         result="composite2" />
    </filter>
  </defs>
'''

style = 'filter:url(#dropshadow);'
