import React from 'react'

const CustomComp = React.forwardRef<HTMLDivElement, any>((props, ref) => (
  <div ref={ref} {...props} />
))

export default CustomComp
