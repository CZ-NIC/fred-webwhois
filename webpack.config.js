const path = require('path')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')

module.exports = {
    mode: 'production',
    stats: {
        children: true,
    },
    entry: {
        'js/main': path.resolve(__dirname, 'assets/js/main.js'),
        'css/main': path.resolve(__dirname, 'assets/scss/main.scss'),
    },
    output: {
        filename: '[name].js',
        path: path.resolve(__dirname, 'webwhois/static/webwhois'),
    },
    devtool: 'source-map',
    module: {
        rules: [{
            test: /\.js$/,
            include: path.join(__dirname, 'assets/js'),
            exclude: /node_modules/,
            use: {
                loader: 'babel-loader',
            },
        }, {
            test: /\.s?css$/,
            use: [
                MiniCssExtractPlugin.loader,
                'css-loader',
                'postcss-loader',
                {
                    loader: 'sass-loader',
                    options: { implementation: require('sass'),
                    },
                },
            ],
        }, {
            test: /\.(png|svg|jpe?g|gif)$/,
            use: [
                {
                    loader: 'file-loader',
                    options: {
                        name: '[name].[ext]',
                        outputPath: 'img/',
                        publicPath: '../img/',
                    },
                },
            ],
        }, {
            test: /\.(woff|woff2|eot|ttf|)$/,
            use: [
                {
                    loader: 'file-loader',
                    options: {
                        name: '[name].[ext]',
                        outputPath: 'font/',
                        publicPath: '../font/',
                    },
                },
            ],
        }],
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: '[name].css',
            chunkFilename: '[id].css',
        }),
    ],
}
