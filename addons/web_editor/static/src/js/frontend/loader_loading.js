(function () {
'use strict';

/**
 * This file makes sure textarea elements with a specific editor class are
 * tweaked as soon as the DOM is ready so that they appear to be loading.
 *
 * They must then be loaded using standard Odoo modules system. In particular,
 * @see web_editor.loader
 */

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('textarea.o_wysiwyg_loader').forEach(textarea => {
        var wrapper = document.createElement('div');
        wrapper.classList.add('position-relative', 'o_wysiwyg_wrapper');

        var loadingElement = document.createElement('div');
        loadingElement.classList.add('o_wysiwyg_loading');
        var loadingIcon = document.createElement('i');
        loadingIcon.classList.add('text-600', 'text-center',
            'fa', 'fa-circle-o-notch', 'fa-spin', 'fa-2x');
        loadingElement.appendChild(loadingIcon);
        wrapper.appendChild(loadingElement);

        textarea.parentNode.insertBefore(wrapper, textarea);
        wrapper.insertBefore(textarea, loadingElement);
    });
});

})();