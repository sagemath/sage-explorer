var MyHTMLModel = /** @class */ (function (_super) {
    __extends(MyHTMLModel, _super);
    function MyHTMLModel() {
        return _super !== null && _super.apply(this, arguments) || this;
    }
    MyHTMLModel.prototype.defaults = function () {
        return _.extend(_super.prototype.defaults.call(this), {
            _view_name: 'HTMLView',
            _model_name: 'MyHTMLModel'
        });
    };
    return MyHTMLModel;
}(HTMLModel));
alert('ok')
//exports.MyHTMLModel = MyHTMLModel;
