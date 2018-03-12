import { h } from 'preact'
import {shallow} from 'preact-render-spy'
import * as UI from './UI'

import Header, {
    HeaderMobile,
} from './Header'

describe('<Header />', () => {
    test('Renders HeaderMobile inside wrapper div', () => {
        const header = shallow(<Header />)
        expect(header.find('div').contains(<HeaderMobile />)).toBeTruthy()
    })
})

describe('<HeaderMobile />', () => {
    test('Renders HeaderMobile inside wrapper div', () => {
        const header = shallow(<Header />)
        expect(header.find('div').contains(<HeaderMobile />)).toBeTruthy()
    })
})
