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
 * Save a storage S3
 */
function saveStorageS3() 
{
    let cloudStorageName = document.getElementById("cloudStorage_name_s3").value.trim();
    if (cloudStorageName !== "" && !/\s/.test(cloudStorageName)) {
      let alternateCheckbox = document.getElementById("alternate");
      let msg = {
        cloudstorage_name: cloudStorageName,
        region: document.getElementById("region").value,
        alternate: alternateCheckbox.checked
      };
  
      console.log(msg);
      return $.ajax({
        url: "/config/cloud_storage_s3?",
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        data: JSON.stringify(msg)
      }).done(function(data, textStatus, jqXHR) {
        refreshCloudStorage();
        // Clear the input field
        document.getElementById("cloudStorage_name_s3").value = "";
        document.getElementById("alternate").value = "";
        document.getElementById("region").value = "";
      })
        .fail(function(jqXHR) {
          errorMessage(jqXHR);
        });
    } else {
      console.log("cloudstorage_name is empty or contains spaces!");
      confirm("The storage name cannot be null or contain spaces");
    }
}

/**
 * Delete a storage Gcloud
 */
function saveStorageGcloud() 
{
    let cloudStorageName = document.getElementById("cloudStorage_name_gcloud").value.trim();
    if (cloudStorageName !== "" && !/\s/.test(cloudStorageName)) {
      let msg = new FormData();
      msg.append("cloudstorage_name", cloudStorageName);
      msg.append("auth_file", document.getElementById("auth_file").files[0]);
  
      console.log(msg);
  
      let xhr = new XMLHttpRequest();
      xhr.open("POST", "/config/cloud_storage_gcloud?");
      xhr.send(msg);
      refreshCloudStorage();
      // Clear the input field
      document.getElementById("cloudStorage_name_gcloud").value = "";
      document.getElementById("auth_file").value = null;
    } else {
        confirm("The storage name cannot be null or contain spaces");
    }
}

/**
 * Download a Gcloud Auth file
 */
function downloadAuthFile(cloudStorage_name)
{
    var link = document.createElement('a');
    var url = window.location.origin;
    link.href = url + "/config/gcloud_auth_file/" + encodeURIComponent(cloudStorage_name);
    console.log(url)
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Delete a storage Swift
 */
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
        }).done(function(data, textStatus, jqXHR) {
            refreshCloudStorage();
            // Clear the input field
            document.getElementById("cloudStorage_name_swift").value = "";
            document.getElementById("os_project_id").value = "";
            document.getElementById("os_token").value = "";
        })
        .fail(function(jqXHR) {
            errorMessage(jqXHR);
        });
    }
}

/**
 * Delete a storage S3
 */
function deleteStorageS3(cloudStorage_name, div)
{
    // div.css("background", "#d9534f");
    $.ajax({
        url: "/config/cloud_storage_s3/" + encodeURIComponent(cloudStorage_name),
        type: "DELETE",
        dataType: "json",
        contentType: "application/json"
    })
    .done(function(data, textStatus, jqXHR) {
        // div.fadeOut(300, function() {$("#").remove();})
        refreshCloudStorage();
    })
    .fail(function(jqXHR) {
        errorMessage(jqXHR);
    });
    // .always(function() {
    //     // div.css("background", "#ffffff").css("transition", "background .50s ease-in-out");
    // });
}

/**
 * Delete a storage Gcloud
 */
function deleteStorageGcloud(cloudStorage_name, div)
{
    // div.css("background", "#d9534f");
    $.ajax({
        url: "/config/cloud_storage_gcloud/" + encodeURIComponent(cloudStorage_name),
        type: "DELETE",
        dataType: "json",
        contentType: "application/json"
    })
    .done(function(data, textStatus, jqXHR) {
        // div.fadeOut(300, function() {div.remove();})
        refreshCloudStorage();
    })
    .fail(function(jqXHR) {
        errorMessage(jqXHR);
    });
    // .always(function() {
    //     div.css("background", "#ffffff").css("transition", "background .50s ease-in-out");
    // });
}

/**
 * Delete storage Swift
 */
function deleteStorageSwift(cloudStorage_name, div)
{
    // div.css("background", "#d9534f");
    $.ajax({
        url: "/config/cloud_storage_swift/" + encodeURIComponent(cloudStorage_name),
        type: "DELETE",
        dataType: "json",
        contentType: "application/json"
    })
    .done(function(data, textStatus, jqXHR) {
        // div.fadeOut(300, function() {div.remove();})
        refreshCloudStorage();
    })
    .fail(function(jqXHR) {
        errorMessage(jqXHR);
    });
    // .always(function() {
    //     div.css("background", "#ffffff").css("transition", "background .50s ease-in-out");
    // });
}

/**
 * Save a user S3
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
    if (!msg.user_dn || /^\s*$/.test(msg.user_dn)){
        confirm("The user cannot be null or contain spaces");
    } else if (!msg.vo_name || /^\s*$/.test(msg.vo_name)){
        confirm("The vo_name cannot be null or contain spaces");
    }
    else {
        return $.ajax({
            url: "/config/cloud_storage/" + encodeURIComponent(cloudStorage_name),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify(msg)
        });
    }
}

/**
 * Save a user Gcloud
 */
function saveUserGcloud(cloudStorage_name, form)
{
    var msg = {
        user_dn: form.find("input[name='user-dn']").val(),
        vo_name: form.find("input[name='vo-name']").val()
    };

    if (!msg.user_dn || /^\s*$/.test(msg.user_dn)){
        confirm("The user cannot be null or contain spaces");
    } else if (!msg.vo_name || /^\s*$/.test(msg.vo_name)){
        confirm("The vo_name cannot be null or contain spaces");
    }
    else {
        return $.ajax({
            url: "/config/cloud_storage/" + encodeURIComponent(cloudStorage_name),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify(msg)
        });
    }
}

/**
 * Save a user Gcloud
 */
function saveUserSwift(cloudStorage_name, form)
{
    var msg = {
        user_dn: form.find("input[name='user-dn']").val(),
        vo_name: form.find("input[name='vo-name']").val()
    };

    console.log(msg);
    if (!msg.user_dn || /^\s*$/.test(msg.user_dn)){
        confirm("The user cannot be null or contain spaces");
    } else if (!msg.vo_name || /^\s*$/.test(msg.vo_name)){
        confirm("The vo_name cannot be null or contain spaces");
    }
    else {
        return $.ajax({
            url: "/config/cloud_storage/" + encodeURIComponent(cloudStorage_name),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify(msg)
        });
    }
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
                    div.find(".user-entry-s3").each(function () {
                        var tr = $(this);
                        var deleteUserBtn = tr.find(".btn-delete-user");
                        deleteUserBtn.click(function (event) {
                            event.preventDefault();
                            deleteUser(storage.cloudStorage_name, tr);
                        });
                        // var saveUserBtn = tr.find(".btn-save-user");
                        // saveUserBtn.click(function (event) {
                        //     event.preventDefault();
                        //     saveUser(storage.storage_name, tr)
                        // });
                    });
                }

                if (storage.cloud_type === "gcloud") {

                    var div = $(template_cloud_storage_gcloud_entry(storage));

                    // Attach to the delete button
                    var deleteBtn = div.find(".btn-delete-gcloud");
                    deleteBtn.click(function (event) {
                        event.preventDefault();
                        deleteStorageGcloud(storage.cloudStorage_name, div);
                    });

                    // Attach to the download auth file button
                    var authDwLnk = div.find(".lnk-auth-dw");
                    authDwLnk.click(function (event) {
                        event.preventDefault();
                        downloadAuthFile(storage.cloudStorage_name);
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
                    var addUserFrm = div.find(".frm-add-user-gcloud");
                    var addUserBtn = addUserFrm.find(".btn-add-user-gcloud");
                    addUserBtn.click(function (event) {
                        event.preventDefault();
                        saveUserGcloud(storage.cloudStorage_name, addUserFrm)
                            .done(function (data, textStatus, jqXHR) {
                                refreshCloudStorage();
                            })
                            .fail(function (jqXHR) {
                                errorMessage(jqXHR);
                            });
                    });
                    // Attach to remove and modify a user
                    div.find(".user-entry-gcloud").each(function () {
                        var tr = $(this);
                        var deleteUserBtn = tr.find(".btn-delete-user");
                        deleteUserBtn.click(function (event) {
                            event.preventDefault();
                            deleteUser(storage.cloudStorage_name, tr);
                        });
                        // var saveUserBtn = tr.find(".btn-save-user");
                        // saveUserBtn.click(function (event) {
                        //     event.preventDefault();
                        //     saveUser(storage.storage_name, tr)
                        // });
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
                    var addUserFrm = div.find(".frm-add-user-swift");
                    var addUserBtn = addUserFrm.find(".btn-add-user-swift");
                    addUserBtn.click(function (event) {
                        event.preventDefault();
                        saveUserSwift(storage.cloudStorage_name, addUserFrm)
                            .done(function (data, textStatus, jqXHR) {
                                refreshCloudStorage();
                            })
                            .fail(function (jqXHR) {
                                errorMessage(jqXHR);
                            });
                    });

                    // Attach to remove and modify a user
                    div.find(".user-entry-swift").each(function () {
                        var tr = $(this);
                        var deleteUserBtn = tr.find(".btn-delete-user");
                        deleteUserBtn.click(function (event) {
                            event.preventDefault();
                            deleteUser(storage.cloudStorage_name, tr);
                        });
                        // var saveUserBtn = tr.find(".btn-save-user");
                        // saveUserBtn.click(function (event) {
                        //     event.preventDefault();
                        //     saveUser(storage.storage_name, tr)
                        // });
                    });
                }
            parent.append(div);
            }
        });
        // Get the dropdown element
        let dropdown = document.getElementById("cs-dropdown");
        // Clear the selection
        dropdown.selectedIndex = -1;
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

/**
* Dropdown selection
 */
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
