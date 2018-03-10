import { h } from 'preact'
import {shallow} from 'preact-render-spy'

import Header from './Header'

describe('Header', () => {
    test('<Header />', () => {
        const header = shallow(<Header />)
        expect(header.find('div').contains(<span>Hello, world!</span>)).toBeTruthy()
    })
})
