import { h, render } from 'preact'

const foo = () => {
    const what = 'bar'

    render((
        <div id="foo">
            <span>Hello, world!</span>
            <button onClick={ e => alert("hi!") }>Click Me</button>
        </div>
    ), document.body)
}

export default foo
