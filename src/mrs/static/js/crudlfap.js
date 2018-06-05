/* global Raven */
// Add our controllers to crudlfap's

import { definitionsFromContext } from 'stimulus/webpack-helpers'
import application from 'crudlfap/js/index.js'

var context = require.context('./controllers', true, /\.js$/)
application.load(definitionsFromContext(context))

application.handleError = (error, message, detail) => {
  if (console.warn !== undefined) console.warn(message, detail) // eslint-disable-line no-console
  if (Raven !== undefined) Raven.captureException(error)
}
