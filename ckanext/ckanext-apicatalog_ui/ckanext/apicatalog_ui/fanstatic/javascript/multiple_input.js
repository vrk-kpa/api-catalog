function createRemoveLink(inputContainer) {
    // The remove link with the icon
    var removeLink = $('<a href="javascript:void(0);" class="multiple-values-remove-input"><span class="fa fa-remove"></span></a>');
    // Add an event listener for removing the input field container
    removeLink.click(function() {
        // Remove the value inside the container's input field
        inputContainer.find('> input').val("");
        // Remove the container
        inputContainer.remove();
        return false;
    });
    // Append the remove link to the input container
    inputContainer.append(removeLink);
    return removeLink;
}


$(document).ready(function() {
    /* Create an add link for all the multiple-values child div elements. The add link clones the input container. */
    $('.multiple-values').each(function() {
        var listContainer = $(this);
        // Loop through all the children divs inside multiple-values
        listContainer.children('div').each(function(valueIndex) {
            if (valueIndex == 0) {
                var inputContainer = $(this);
                var addLinkName = listContainer.attr('data-add-input');
                var addLink = addLinkName && $(`[name="${addLinkName}"]`);
                if (!addLink) {
                  // We are adding the 'add link' only to the first child
                  addLink = $('<a href="javascript:void(0);" class="multiple-values-add-input"><span class="fa fa-plus"></span></a>');
                  inputContainer.append(addLink);
                }

                addLink.click(function() {
                    var clonedInputContainer = inputContainer.clone();
                    clonedInputContainer.find('> input').val("").removeAttr('id');
                    clonedInputContainer.find('> a').remove();
                    createRemoveLink(clonedInputContainer);
                    listContainer.append(clonedInputContainer);
                    return false;
                });
            } else {
                // We are adding the remove link to all the other children
                createRemoveLink($(this));
            }
        });
    });
});

