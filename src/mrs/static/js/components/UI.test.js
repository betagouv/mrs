import React from 'react'
import {shallow} from 'enzyme'

import * as UI from './UI'

describe('<Flex />', () => {
  test('renders children', () => {
    const Child = () => <div>Hello</div>
    const subject = shallow(<UI.Flex><Child /></UI.Flex>)

    expect(subject .find('div').contains(<Child />)).toBeTruthy()
  })

  test('renders w/ proper css classes', () => {
    const subject1 = shallow(<UI.Flex></UI.Flex>)
    const subject2 = shallow(<UI.Flex className="foo"></UI.Flex>)

    expect(subject1.find('div.ui.flex')).toBeTruthy()
    expect(subject2.find('div.ui.flex.foo')).toBeTruthy()
  })
})

describe('<Column />', () => {
  test('renders children', () => {
    const Child = () => <div>Hello</div>
    const subject = shallow(<UI.Column><Child /></UI.Column>)

    expect(subject .find(UI.Flex).contains(<Child />)).toBeTruthy()
  })

  test('renders w/ proper css classes', () => {
    const subject1 = shallow(<UI.Column></UI.Column>)
    const subject2 = shallow(<UI.Column className="foo"></UI.Column>)

    expect(subject1.find('div.ui.flex.column')).toBeTruthy()
    expect(subject2.find('div.ui.flex.column.foo')).toBeTruthy()
  })
})

describe('<Row />', () => {
  test('renders children', () => {
    const Child = () => <div>Hello</div>
    const subject = shallow(<UI.Row><Child /></UI.Row>)

    expect(subject .find(UI.Flex).contains(<Child />)).toBeTruthy()
  })

  test('renders w/ proper css classes', () => {
    const subject1 = shallow(<UI.Row></UI.Row>)
    const subject2 = shallow(<UI.Row className="foo"></UI.Row>)

    expect(subject1.find('div.ui.flex.column')).toBeTruthy()
    expect(subject2.find('div.ui.flex.column.foo')).toBeTruthy()
  })
})
