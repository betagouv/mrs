import { h } from 'preact'

const Flex = props => {
    const className = "ui flex " + props.className

    return (
        <div className={ className }>
          { props.children }
        </div>
    )
}

Flex.defaultProps = {
    className: "",
}

const Column = props => {
    const className = "column " + props.className

    return (
        <Flex className={ className }>
          { props.children }
        </Flex>
    )
}

Column.defaultProps = {
    className: "",
}

const Row = props => {
    const className = "row " + props.className

    return (
        <Flex className={ className }>
          { props.children }
        </Flex>
    )
}

Row.defaultProps = {
    className: "",
}


export {
    Column,
    Flex,
    Row,
}
