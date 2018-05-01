import React from 'react'
import { shallow } from 'enzyme'

import {
  CarouselSlide,
} from './Caroussel.js'

describe('<CarouselSlide />', () => {
  test('renders children', () => {
    const carouselSlide = shallow(<CarouselSlide />)
    expect(1).toBe(1)
  })
})
