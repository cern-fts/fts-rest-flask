/*
 *  Copyright 2015 CERN
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
**/

/** Template as globals */
var template_cloud_storage_entry = null;

/**
 * Save a new storage, or change it
 */
function saveStorageS3()
{
    let alternateCheckbox = document.getElementById("alternate");
    var msg = {
        cloudstorage_name: document.getElementById("cloudStorage_name_s3").value,
        region:  document.getElementById("region").value,
        alternate: alternateCheckbox.checked
    };

    console.log(msg);
    if (!msg.cloudstorage_name || /^\s*$/.test(msg.cloudstorage_name)){
        confirm("The storage name cannot be null or contain spaces");
    }
    else {
        return $.ajax({
            url: "/config/cloud_storage_s3?",
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify(msg)
        });
    }
}

function saveStorageGcloud()
{
    let msg = new FormData();
    msg.append("cloudstorage_name",document.getElementById("cloudStorage_name_gcloud").value);
    msg.append("auth_file",document.getElementById("auth_file").files[0] );

    console.log(msg);

    let xhr = new XMLHttpRequest();
    xhr.open("POST","/config/cloud_storage_gcloud?" );
    xhr.send(msg);
}

function saveStorageSwift()
{
    var msg = {
        cloudstorage_name: document.getElementById("cloudStorage_name_swift").value,
        os_project_id:  document.getElementById("os_project_id").value,
        os_token:  document.getElementById("os_token").value
    };
    console.log(msg);

    if (!msg.cloudstorage_name || /^\s*$/.test(msg.cloudstorage_name)){
        confirm("The storage name cannot be null or contain spaces");
    }
    else {
        return $.ajax({
            url: "/config/cloud_storage_swift?",
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify(msg)
        });
    }
    location.reload();
}

/**
 * Delete a storage
 */
function deleteStorageS3(cloudStorage_name, div)
{
    div.css("background", "#d9534f");
    $.ajax({
        url: "/config/cloud_storage_s3/" + encodeURIComponent(cloudStorage_name),
        type: "DELETE",
        dataType: "json",
        contentType: "application/json"
    })
    .done(function(data, textStatus, jqXHR) {
        div.fadeOut(300, function() {div.remove();})
    })
    .fail(function(jqXHR) {
        errorMessage(jqXHR);
    })
    .always(function() {
        div.css("background", "#ffffff").css("transition", "background .50s ease-in-out");
    });
}

/**
 * Delete a storage
 */
function deleteStorageGcloud(cloudStorage_name, div)
{
    div.css("background", "#d9534f");
    $.ajax({
        url: "/config/cloud_storage_gcloud/" + encodeURIComponent(cloudStorage_name),
        type: "DELETE",
        dataType: "json",
        contentType: "application/json"
    })
    .done(function(data, textStatus, jqXHR) {
        div.fadeOut(300, function() {div.remove();})
    })
    .fail(function(jqXHR) {
        errorMessage(jqXHR);
    })
    .always(function() {
        div.css("background", "#ffffff").css("transition", "background .50s ease-in-out");
    });
}

/**
 * Delete a storage
 */
function deleteStorageSwift(cloudStorage_name, div)
{
    div.css("background", "#d9534f");
    $.ajax({
        url: "/config/cloud_storage_swift/" + encodeURIComponent(cloudStorage_name),
        type: "DELETE",
        dataType: "json",
        contentType: "application/json"
    })
    .done(function(data, textStatus, jqXHR) {
        div.fadeOut(300, function() {div.remove();})
    })
    .fail(function(jqXHR) {
        errorMessage(jqXHR);
    })
    .always(function() {
        div.css("background", "#ffffff").css("transition", "background .50s ease-in-out");
    });
}

/**
 * Save a user
 */
function saveUserS3(cloudStorage_name, form)
{
    var msg = {
        user_dn: form.find("input[name='user-dn']").val(),
        vo_name: form.find("input[name='vo-name']").val(),
        access_key: form.find("input[name='access-key']").val(),
        secret_key: form.find("input[name='secret-key']").val()
    };

    console.log(msg);

    return $.ajax({
        url: "/config/cloud_storage/" + encodeURIComponent(storage_name),
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        data: JSON.stringify(msg)
    });
}

/**
 * Delete a user
 */
function deleteUser(storage_name, form)
{
    var user_dn = form.find("input[name='user-dn']").val();
    var vo_name = form.find("input[name='vo-name']").val();
    var id;
    if (user_dn)
        id = encodeURIComponent(user_dn);
    else
        id = encodeURIComponent(vo_name);

    $.ajax({
        url: "/config/cloud_storage/" + encodeURIComponent(storage_name) + "/" + id,
        type: "DELETE",
        dataType: "json",
        contentType: "application/json"
    })
    .done(function(data, textStatus, jqXHR) {
        form.fadeOut(300, function() {form.remove();})
    })
    .fail(function(jqXHR) {
        errorMessage(jqXHR);
    })
    .always(function() {
        form.css("background", "#ffffff").css("transition", "background .50s ease-in-out");
    });
}

/**
 * Refresh the storage list
 */
function refreshCloudStorage()
{
    var parent = $("#storage-list");

    $.ajax({
        headers: {
            Accept : "application/json",
        },
        url: "/config/cloud_storage?",
    })
    .done(function(data, textStatus, jqXHR) {
        parent.empty();
        $.each(data, function(index, storage_list) {
            console.log(storage_list);
            for (let i = 0; i < storage_list.length; i++) {
                let storage = storage_list[i]
                console.log(storage)

                /* if type:
                    s3 --> template_cloud_storage_s3_entry
                    gcloud --> template_cloud_storage_gcloud_entry
                    swift --> template_cloud_storage_swift_entry
                */
                if (storage.cloud_type === "S3") {

                    var div = $(template_cloud_storage_s3_entry(storage));

                    // Attach to the delete button
                    var deleteBtn = div.find(".btn-delete-s3");
                    deleteBtn.click(function (event) {
                        event.preventDefault();
                        deleteStorageS3(storage.cloudStorage_name, div);
                    });

                    // Attach to the save button
                    var saveBtn = div.find(".btn-save-s3");
                    saveBtn.click(function (event) {
                        event.preventDefault();
                        saveStorageS3(div)
                            .fail(function (jqXHR) {
                                errorMessage(jqXHR);
                            });
                    });

                    // Attach to add a user
                    var addUserFrm = div.find(".frm-add-user-s3");
                    var addUserBtn = addUserFrm.find(".btn-add-user-s3");
                    addUserBtn.click(function (event) {
                        event.preventDefault();
                        saveUserS3(storage.cloudStorage_name, addUserFrm)
                            .done(function (data, textStatus, jqXHR) {
                                refreshCloudStorage();
                            })
                            .fail(function (jqXHR) {
                                errorMessage(jqXHR);
                            });
                    });

                    // Attach to remove and modify a user
                    div.find(".user-entry").each(function () {
                        var tr = $(this);
                        var deleteUserBtn = tr.find(".btn-delete-user");
                        deleteUserBtn.click(function (event) {
                            event.preventDefault();
                            deleteUser(storage.storage_name, tr);
                        });
                        var saveUserBtn = tr.find(".btn-save-user");
                        saveUserBtn.click(function (event) {
                            event.preventDefault();
                            saveUser(storage.storage_name, tr)
                        });
                    });
                }

                if (storage.cloud_type === "gcloud") {

                    var div = $(template_cloud_storage_gcloud_entry(storage));

                    // Attach to the delete button
                    var deleteBtn = div.find(".btn-delete-Gcloud");
                    deleteBtn.click(function (event) {
                        event.preventDefault();
                        deleteStorageGcloud(storage.cloudStorage_name, div);
                    });

                    // Attach to the save button
                    var saveBtn = div.find(".btn-save");
                    saveBtn.click(function (event) {
                        event.preventDefault();
                        saveStorage(div)
                            .fail(function (jqXHR) {
                                errorMessage(jqXHR);
                            });
                    });

                    // Attach to add a user
                    var addUserFrm = div.find(".frm-add-user");
                    var addUserBtn = addUserFrm.find(".btn-add-user");
                    addUserBtn.click(function (event) {
                        event.preventDefault();
                        saveUser(storage.storage_name, addUserFrm)
                            .done(function (data, textStatus, jqXHR) {
                                refreshCloudStorage();
                            })
                            .fail(function (jqXHR) {
                                errorMessage(jqXHR);
                            });
                    });

                    // Attach to remove and modify a user
                    div.find(".user-entry").each(function () {
                        var tr = $(this);
                        var deleteUserBtn = tr.find(".btn-delete-user");
                        deleteUserBtn.click(function (event) {
                            event.preventDefault();
                            deleteUser(storage.storage_name, tr);
                        });
                        var saveUserBtn = tr.find(".btn-save-user");
                        saveUserBtn.click(function (event) {
                            event.preventDefault();
                            saveUser(storage.storage_name, tr)
                        });
                    });
                }
                if (storage.cloud_type === "swift") {

                    var div = $(template_cloud_storage_swift_entry(storage));

                    // Attach to the delete button
                    var deleteBtn = div.find(".btn-delete-Swift");
                    deleteBtn.click(function (event) {
                        event.preventDefault();
                        deleteStorageSwift(storage.cloudStorage_name, div);
                    });

                    // Attach to the save button
                    var saveBtn = div.find(".btn-save");
                    saveBtn.click(function (event) {
                        event.preventDefault();
                        saveStorage(div)
                            .fail(function (jqXHR) {
                                errorMessage(jqXHR);
                            });
                    });

                    // Attach to add a user
                    var addUserFrm = div.find(".frm-add-user");
                    var addUserBtn = addUserFrm.find(".btn-add-user");
                    addUserBtn.click(function (event) {
                        event.preventDefault();
                        saveUser(storage.storage_name, addUserFrm)
                            .done(function (data, textStatus, jqXHR) {
                                refreshCloudStorage();
                            })
                            .fail(function (jqXHR) {
                                errorMessage(jqXHR);
                            });
                    });

                    // Attach to remove and modify a user
                    div.find(".user-entry").each(function () {
                        var tr = $(this);
                        var deleteUserBtn = tr.find(".btn-delete-user");
                        deleteUserBtn.click(function (event) {
                            event.preventDefault();
                            deleteUser(storage.storage_name, tr);
                        });
                        var saveUserBtn = tr.find(".btn-save-user");
                        saveUserBtn.click(function (event) {
                            event.preventDefault();
                            saveUser(storage.storage_name, tr)
                        });
                    });
                }
            parent.append(div);
            }
        });
    })
    .fail(function(jqXHR) {
        errorMessage(jqXHR);
    });
}

/**
 * Compile templates embedded into the HTML
 */
function compileTemplates()
{
    template_cloud_storage_s3_entry = Handlebars.compile(
        $("#s3-storage-entry-template").html()
    );
    template_cloud_storage_gcloud_entry = Handlebars.compile(
        $("#gcloud-storage-entry-template").html()
    );
    template_cloud_storage_swift_entry = Handlebars.compile(
        $("#swift-storage-entry-template").html()
    );
}
function selectCloudStorage() {
    $(document).ready(function(){
        $("select").change(function(){
            $(this).find("option:selected").each(function(){
                let optionValue = $(this).attr("value");
                if(optionValue){
                    $(".endpoint").not("." + optionValue).hide();
                    $("." + optionValue).show();
                } else{
                    $(".endpoint").hide();
                }
            });
        }).change();
    });
}
/**
* Enables dropdown visibility
 */
window.onload = cs_dropdown;
function cs_dropdown(){
    document
    .getElementById('cs-dropdown')
    .addEventListener('change', function () {
        'use strict';
        let vis = document.querySelector('.vis'),
            target = document.getElementById(this.value);
        if (vis !== null) {
            vis.className = 'inv';
        }
        if (target !== null ) {
            target.className = 'vis';
        }
});
}
/**
 * Initializes the SE view
 */
function setupCloudStorage()
{
    // Add Handlebar custom ifCondition
    Handlebars.registerHelper('ifCond', function(v1, v2, options) {
  if(v1 === v2) {
    return options.fn(this);
  }
  return options.inverse(this);
});
    selectCloudStorage();
    compileTemplates();
    refreshCloudStorage();

    // Bind to form
    $("#add-cloud-frm").submit(function(event) {
        event.preventDefault();
        saveStorage($("#add-cloud-frm"))
        .done(function(data, textStatus, jqXHR) {
            $("#add-cloud-frm").trigger("reset");
            refreshCloudStorage();
        })
        .fail(function(jqXHR) {
            errorMessage(jqXHR);
        });
    });
}
