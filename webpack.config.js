var path = require('path')
var BundleTracker = require('webpack-bundle-tracker')

module.exports = {
  context: __dirname,
  entry: ['babel-polyfill', './src/mrs/static/js/main'],
  output: {
    path: path.resolve('./src/mrs/static/webpack_bundles/'),
    filename: '[name]-[hash].js'
  },

  plugins: [
    new BundleTracker({filename: './webpack-stats.json'})
  ],

  module: {
    rules: [
      {
        test: /\.js$/,
        //exclude: /(node_modules|bower_components)/,
        use: {
          loader: 'babel-loader',
          options: {
              presets: ['stage-2', 'babel-preset-env']
          }
        }
      }
    ]
  }
}
