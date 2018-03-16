import { h as React } from 'preact'
import { shallow } from 'preact-render-spy'

import Carousel, {
    CarouselDumb,
    CarouselSlide,
    CitationSlide,
    CarouselUI,
} from './Caroussel.test.js'

describe('<CarouselSlide />', () => {
    test('renders children', () => {
        const carouselSlide = shallow(<CarouselSlide />)
    })
})
