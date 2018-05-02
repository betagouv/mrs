// Add our controllers to crudlfap's

import { Application } from 'stimulus'
import { definitionsFromContext } from 'stimulus/webpack-helpers'
import Crudlfap from 'crudlfap/js'

(() => {
  if (window.Turbolinks === undefined) {
    var Turbolinks = require('turbolinks')
    Turbolinks.start()
  }
}).bind(window)()

const application = Application.start()
var context = require.context('./controllers', true, /\.js$/)
application.load(definitionsFromContext(context))

Crudlfap()