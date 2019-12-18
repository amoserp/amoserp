odoo.define('product_product_button', function (require) {
"use strict";
var view_registry = require('web.view_registry');
var ListController = require('web.ListController');
var ListView = require('web.ListView');
var rpc = require('web.rpc');

function boxRenderButtons($node) {
        var self = this;
        this.$buttons = $('<div/>');
        this.$buttons.html('<button class="btn btn-primary type="button">Confirm</button>');
        this.$buttons.on('click', function () {
            var state = self.model.get(self.handle, {raw: true});
            //state.res_ids   all ids
            var records = self.getSelectedRecords();
            var values = _.map(records, function (record) {
                            return record.res_id;
                        });
            // trace(values);
            rpc.query({
                    model: self.modelName,
                    method: 'button_add_batch',
                    args: [{'model': self.modelName}],
                    context: {params:state.getContext(),res_ids: values}, // TODO use this._rpc
                });

        });
        this.$buttons.appendTo($node);

}



var BoxListController = ListController.extend({
    renderButtons: function ($node) {
        return boxRenderButtons.apply(this, arguments);
    },
});

var BoxListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: BoxListController,
    }),
});

view_registry.add('product_product_button_list_view', BoxListView);


});