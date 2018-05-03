// Add our controllers to crudlfap's

import { definitionsFromContext } from 'stimulus/webpack-helpers'
import application from 'crudlfap/js/index.js'

var context = require.context('./controllers', true, /\.js$/)
application.load(definitionsFromContext(context))
