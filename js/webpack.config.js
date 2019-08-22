const path = require('path');
const version = require('./package.json').version;

const rules = [
  { test: /\.ts$/, loader: 'ts-loader' },
  { test: /\.js$/, loader: 'source-map-loader' },
  { test: /\.css$/, use: ['style-loader', 'css-loader']},
  { test: /\.(jpg|png|gif)$/, use: ['url-loader']}
];

const externals = ['@jupyter-widgets/base', '@jupyter-widgets/controls']

const resolve = {
  extensions: [".webpack.js", ".web.js", ".ts", ".js"]
};

module.exports = [
  { // Notebook extension
    entry: './src/extension.ts',
    output: {
      filename: 'index.js',
      path: path.resolve(__dirname, 'new_sage_explorer', 'nbextension', 'static'),
      libraryTarget: 'amd'
    },
    module: {
      rules: rules
    },
    devtool: 'source-map',
    externals,
    resolve,
  },

  { // Embeddable new-sage-explorer bundle
    entry: './src/index.ts',
    output: {
        filename: 'index.js',
        path: path.resolve(__dirname, 'dist'),
        libraryTarget: 'amd',
        library: "new-sage-explorer",
        publicPath: 'https://unpkg.com/new-sage-explorer@' + version + '/dist/'
    },
    devtool: 'source-map',
    module: {
        rules: rules
    },
    externals,
    resolve,
  },

  { // Documentation widget bundle
    entry: './src/index.ts',
    output: {
      filename: 'embed-bundle.js',
      path: path.resolve(__dirname, 'docs', 'source', '_static'),
      library: "new-sage-explorer",
      libraryTarget: 'amd'
    },
    module: {
      rules: rules
    },
    devtool: 'source-map',
    externals,
    resolve,
  }

];
