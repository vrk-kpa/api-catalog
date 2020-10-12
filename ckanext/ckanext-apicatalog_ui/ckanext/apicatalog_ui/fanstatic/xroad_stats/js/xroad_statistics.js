'use strict';

/* xroad_statistics
 *
 * This JavaScript module thingamajig is rather heavily modified version of
 * https://github.com/TaaviMeinberg/TaaviMeinberg.github.io X-Road Environment Dashboard
 * and it draws pretty graphs based on data pulled from x-road-statistics API
 * (https://app.swaggerhub.com/apis-docs/NIIS/x-road-statistics/1.0.0#/)
 *
 */

ckan.module('xroad_statistics', function ($) {
  let graphsArray = [];

  return {
    initialize: function () {
      // Buttons are initially disabled until this module loads as they wouldn't function before that anyways
      this.el.prop("disabled", false);

      // Add an event handler to the button, when the user clicks the button
      // our _onClick() function will be called.
      this.el.on('click', jQuery.proxy(this._onClick, this));

      // Initialize view with 'FI' env data by default
      this.drawDiagrams('FI');
    },

    _onClick: function(e) {
      e.preventDefault();
      this.drawDiagrams(e.target.value);
    },

    drawDiagrams: function (env) {
      // Destroy existing charts
      graphsArray.map((chart) => chart.destroy())
      // Clean array of saved graphs
      graphsArray = [];

      const collection = this.options.statsCollection[env];

      const stats = collection.stats;

      this.getDateAndInstance(stats);
      this.generateMembersDoughnutGraph(stats);
      this.generateEnvironmentTotalsGraph(stats);

      const history = collection.history;

      this.generateSubsystemsTimelineGraph(history, stats);
      this.generateSecurityServersTimelineGraph(history, stats);
      this.generateMembersTimelineGraph(history, stats);
      this.displayYearlyChange(env, history, stats);

      this.setEnvButton(env);
    },

    setEnvButton: function (env) {
      switch (env) {
        case 'FI-TEST':
          $('.btn-env').each(function (index) {
            $(this).removeClass('active');
          });
          $('#testButton').addClass('active');
          break;

        case 'FI':
          $('.btn-env').each(function (index) {
            $(this).removeClass('active');
          });
          $('#prodButton').addClass('active');
          break;
      }
    },

    generateMembersDoughnutGraph: function (resultsJson) {
      let memberClassLabels = [];
      let memberClassData = [];

      if (resultsJson != null) {
        let sortedMemberClasses = resultsJson.memberClasses.sort(function (
          a,
          b,
        ) {
          return parseFloat(b.memberCount) - parseFloat(a.memberCount);
        });
        for (let i in sortedMemberClasses) {
          switch (sortedMemberClasses[i].memberClass) {
            case 'COM':
              memberClassLabels.push('Commercial members');
              memberClassData.push(sortedMemberClasses[i].memberCount);
              break;
            case 'GOV':
              memberClassLabels.push('Governmental members');
              memberClassData.push(sortedMemberClasses[i].memberCount);
              break;
            case 'ORG':
              memberClassLabels.push('Non-profit members');
              memberClassData.push(sortedMemberClasses[i].memberCount);
              break;
            case 'MUN':
              memberClassLabels.push('Municipal members');
              memberClassData.push(sortedMemberClasses[i].memberCount);
              break;
            case 'EDU':
              memberClassLabels.push('Educational members');
              memberClassData.push(sortedMemberClasses[i].memberCount);
              break;
          }
        }
      }

      let ctx = document.getElementById('membersPieCanvas').getContext('2d');
      let membersPieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: memberClassLabels,
          datasets: [
            {
              label: 'Organization distribution',
              data: memberClassData,
              backgroundColor: [
                'rgba(255, 99, 132, 0.8)',
                'rgba(54, 162, 235, 0.8)',
                'rgba(255, 206, 86, 0.8)',
                'rgba(75, 192, 192, 0.8)',
              ],
              borderColor: [
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)',
              ],
              borderWidth: 1,
            },
          ],
        },
        options: {
          plugins: {
            datalabels: {
              font: {
                weight: 'bold',
                size: 20,
              },
              offset: 15,
            },
          },
          title: {
            display: true,
            text: 'Member class distribution',
            fontSize: 16,
          },
          legend: {
            display: true,
            position: 'top',
            labels: {
              boxWidth: 20,
            },
          },
          animation: {
            duration: 0, // general animation time
          },
        },
      });
      graphsArray.push(membersPieChart);
    },

    generateEnvironmentTotalsGraph: function (resultsJson) {
      let environmentTotalsData = [];

      if (resultsJson != null) {
        environmentTotalsData.push(resultsJson.subsystems);
        environmentTotalsData.push(resultsJson.members);
        environmentTotalsData.push(resultsJson.securityServers);
      }

      let ctx = document
        .getElementById('environmentTotalsBarCanvas')
        .getContext('2d');
      let environmentTotalsChart = new Chart(ctx, {
        type: 'horizontalBar',
        data: {
          labels: ['Subsystems', 'Members', 'Security Servers'],
          datasets: [
            {
              label: 'Environment total',
              data: environmentTotalsData,
              backgroundColor: [
                'rgba(26, 163, 255, 0.8)',
                'rgba(255, 99, 132, 0.8)',
                'rgba(255, 206, 86, 0.8)',
              ],
              borderColor: [
                'rgba(26, 163, 255, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(255, 206, 86, 1)',
              ],
              borderWidth: 1,
            },
          ],
        },
        options: {
          plugins: {
            datalabels: {
              font: {
                weight: 'bold',
                size: 20,
              },
              clip: true,
            },
          },
          scales: {
            xAxes: [
              {
                ticks: {
                  beginAtZero: true,
                },
              },
            ],
            yAxes: [
              {
                gridLines: {
                  display: false,
                },
              },
            ],
          },
          legend: {
            display: false,
            labels: {
              fontSize: 18,
            },
          },
          title: {
            display: true,
            text: 'Environment totals',
            fontSize: 16,
          },
          animation: {
            duration: 0, // general animation time
          },
        },
      });

      graphsArray.push(environmentTotalsChart);

    },

    getMaxValue: function (inputArray) {
      return Math.max.apply(Math, inputArray);
    },
    getMinValue: function (inputArray) {
      return Math.min.apply(Math, inputArray);
    },

    getXLatestEntries: function (inputArray, numberOfEntries, interval) {
      let resultArray = [];
      let length = inputArray.length;
      let index = length - 1;
      for (let i = 0; i < numberOfEntries && index >= 0; i++) {
        resultArray.push(inputArray[index]);
        index -= interval;
      }
      return resultArray.reverse();
    },

    generateSubsystemsTimelineGraph: function (metricsJson, stats) {
      let allMetricsDates = [];
      let allMetricsSubsystemsData = [];
      let latestDates = [];
      let latestData = [];

      for (let i in metricsJson) {
        allMetricsDates.push(metricsJson[i].date);
        allMetricsSubsystemsData.push(metricsJson[i].subsystems);
      }
      allMetricsDates.push(stats.date);
      allMetricsSubsystemsData.push(stats.subsystems);

      latestDates = this.getXLatestEntries(allMetricsDates, 12, 1);
      latestData = this.getXLatestEntries(allMetricsSubsystemsData, 12, 1);

      let dataMaxValue = this.getMaxValue(latestData);
      let dataMinValue = this.getMinValue(latestData);
      let ctx = document
        .getElementById('subsystemsTimelineCanvas')
        .getContext('2d');
      let subsystemsTimelineChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: latestDates,
          datasets: [
            {
              data: latestData,
              label: 'Subsystems',
              borderColor: 'rgb(26, 163, 255)',
              fill: true,
              backgroundColor: 'rgba(26, 163, 255, 0.2)',
            },
          ],
        },
        options: {
          title: {
            display: true,
            text: 'Subsystems timeline',
            fontSize: 16,
          },
          scales: {
            yAxes: [
              {
                ticks: {
                  suggestedMax: dataMaxValue + dataMaxValue * 0.2,
                  suggestedMin: dataMinValue - dataMinValue * 0.2,
                },
                gridLines: {
                  display: false,
                },
              },
            ],
          },
          legend: {
            labels: {
              fontSize: 14,
            },
          },
          plugins: {
            datalabels: {
              align: 100,
              anchor: 'start',
              font: {
                weight: 'bold',
                size: 14,
              },
            },
          },
          animation: {
            duration: 0, // general animation time
          },
        },
      });
      graphsArray.push(subsystemsTimelineChart);
    },

    generateMembersTimelineGraph: function (metricsJson, stats) {
      let allMetricsDates = [];
      let allMetricsMembersData = [];
      let latestDates = [];
      let latestData = [];

      if (metricsJson != null) {
        for (let i in metricsJson) {
          allMetricsDates.push(metricsJson[i].date);
          allMetricsMembersData.push(metricsJson[i].members);
        }
      }
      allMetricsDates.push(stats.date);
      allMetricsMembersData.push(stats.members);

      latestDates = this.getXLatestEntries(allMetricsDates, 12, 1);
      latestData = this.getXLatestEntries(allMetricsMembersData, 12, 1);

      let dataMaxValue = this.getMaxValue(latestData);
      let dataMinValue = this.getMinValue(latestData);
      let ctx = document
        .getElementById('membersTimelineCanvas')
        .getContext('2d');
      let membersTimelineChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: latestDates,
          datasets: [
            {
              data: latestData,
              label: 'Members',
              borderColor: 'rgb(255, 99, 132)',
              fill: true,
              backgroundColor: 'rgba(255, 99, 132, 0.2)',
            },
          ],
        },
        options: {
          title: {
            display: true,
            text: 'Members timeline',
            fontSize: 16,
          },
          scales: {
            yAxes: [
              {
                ticks: {
                  suggestedMax: dataMaxValue + dataMaxValue * 0.2,
                  suggestedMin: dataMinValue - dataMinValue * 0.2,
                },
                gridLines: {
                  display: false,
                },
              },
            ],
          },
          legend: {
            labels: {
              fontSize: 14,
            },
          },
          plugins: {
            datalabels: {
              align: 100,
              anchor: 'start',
              font: {
                weight: 'bold',
                size: 14,
              },
            },
            animation: {
              duration: 0, // general animation time
            },
          },
        },
      });
      graphsArray.push(membersTimelineChart);
    },

    generateSecurityServersTimelineGraph: function (metricsJson, stats) {
      let allMetricsDates = [];
      let allMetricsSecurityServersData = [];
      let latestDates = [];
      let latestData = [];

      if (metricsJson != null) {
        for (let i in metricsJson) {
          allMetricsDates.push(metricsJson[i].date);
          allMetricsSecurityServersData.push(metricsJson[i].securityServers);
        }
      }
      allMetricsDates.push(stats.date);
      allMetricsSecurityServersData.push(stats.securityServers);

      latestDates = this.getXLatestEntries(allMetricsDates, 12, 1);
      latestData = this.getXLatestEntries(allMetricsSecurityServersData, 12, 1);

      let dataMaxValue = this.getMaxValue(latestData);
      let dataMinValue = this.getMinValue(latestData);
      let ctx = document
        .getElementById('securityserversTimelineCanvas')
        .getContext('2d');
      let securityServersTimelineChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: latestDates,
          datasets: [
            {
              data: latestData,
              label: 'Security Servers',
              borderColor: 'rgb(255, 206, 86)',
              fill: true,
              backgroundColor: 'rgba(255, 206, 86, 0.2)',
            },
          ],
        },
        options: {
          title: {
            display: true,
            text: 'Security Servers timeline',
            fontSize: 16,
          },
          scales: {
            yAxes: [
              {
                ticks: {
                  suggestedMax: dataMaxValue + dataMaxValue * 0.2,
                  suggestedMin: dataMinValue - dataMinValue * 0.2,
                },
                gridLines: {
                  display: false,
                },
              },
            ],
          },
          legend: {
            labels: {
              fontSize: 14,
            },
          },
          plugins: {
            datalabels: {
              align: 100,
              anchor: 'start',
              font: {
                weight: 'bold',
                size: 14,
              },
            },
          },
          animation: {
            duration: 0, // general animation time
          },
        },
      });
      graphsArray.push(securityServersTimelineChart);
    },

    getDateAndInstance: function (resultsJson) {
      let dateShown = document.getElementById('gatheredDate');
      let environmentShown = document.getElementById('environmentTag');
      let dateGathered;
      let instanceIdentifier;

      if (resultsJson != null) {
        dateGathered = resultsJson.date;
        instanceIdentifier = resultsJson.instanceIdentifier;

        dateShown.textContent = 'Data gathered: ' + dateGathered;
        environmentShown.textContent = 'Environment: ' + instanceIdentifier;
      }
    },

    getStartOfYearValue: function (historyJson, metric) {
      let currentYear = new Date().getFullYear();

      for (let i = 0; i < historyJson.length; i++) {
        if (historyJson[i].date == currentYear + '-01-01') {
          if (metric == 'subsystems') {
            return historyJson[i].subsystems;
          } else if (metric == 'members') {
            return historyJson[i].members;
          } else if (metric == 'securityServers') {
            return historyJson[i].securityServers;
          }
        }
      }
    },

    getCurrentValue: function (currentDataJson, metric) {
      if (metric == 'subsystems') {
        return currentDataJson.subsystems;
      } else if (metric == 'members') {
        return currentDataJson.members;
      } else if (metric == 'securityServers') {
        return currentDataJson.securityServers;
      }
    },

    displayYearlyChange: function (env, historyJson, environmentData) {
      let currentYear = new Date().getFullYear();

      let beginningOfYearSubsystems = this.getStartOfYearValue(
        historyJson,
        'subsystems',
      );
      let beginningOfYearMembers = this.getStartOfYearValue(historyJson, 'members');
      let beginningOfYearServers = this.getStartOfYearValue(
        historyJson,
        'securityServers',
      );

      let currentSubsystems = this.getCurrentValue(environmentData, 'subsystems');
      let currentMembers = this.getCurrentValue(environmentData, 'members');
      let currentServers = this.getCurrentValue(environmentData, 'securityServers');

      //Subsystem yearly change
      $('#subsystemsBeginningValue').text(
        'Beginning of ' + currentYear + ': ' + beginningOfYearSubsystems,
      );
      $('#subsystemsCurrentValue').text('Current value: ' + currentSubsystems);
      if (currentSubsystems > beginningOfYearSubsystems) {
        $('#subsystemsGrowthChange').removeClass();
        $('#subsystemsGrowthChange').addClass('growthMetricPositive');
        $('#subsystemsGrowthChange').text(
          'Change: +' + (currentSubsystems - beginningOfYearSubsystems),
        );
      } else if (currentSubsystems == beginningOfYearSubsystems) {
        $('#subsystemsGrowthChange').removeClass();
        $('#subsystemsGrowthChange').addClass('growthMetricNeutral');
        $('#subsystemsGrowthChange').text('No change');
      } else {
        $('#subsystemsGrowthChange').removeClass();
        $('#subsystemsGrowthChange').addClass('growthMetricNegative');
        $('#subsystemsGrowthChange').text(
          'Change: -' + (beginningOfYearSubsystems - currentSubsystems),
        );
      }

      //Members yearly change
      $('#membersBeginningValue').text(
        'Beginning of ' + currentYear + ': ' + beginningOfYearMembers,
      );
      $('#membersCurrentValue').text('Current value: ' + currentMembers);
      if (currentMembers > beginningOfYearMembers) {
        $('#membersGrowthChange').removeClass();
        $('#membersGrowthChange').addClass('growthMetricPositive');
        $('#membersGrowthChange').text(
          'Change: +' + (currentMembers - beginningOfYearMembers),
        );
      } else if (currentMembers == beginningOfYearMembers) {
        $('#membersGrowthChange').removeClass();
        $('#membersGrowthChange').addClass('growthMetricNeutral');
        $('#membersGrowthChange').text('No change');
      } else {
        $('#membersGrowthChange').removeClass();
        $('#membersGrowthChange').addClass('growthMetricNegative');
        $('#membersGrowthChange').text(
          'Change: -' + (beginningOfYearMembers - currentMembers),
        );
      }

      //Servers yearly change
      $('#serversBeginningValue').text(
        'Beginning of ' + currentYear + ': ' + beginningOfYearServers,
      );
      $('#serversCurrentValue').text('Current value: ' + currentServers);
      if (currentServers > beginningOfYearServers) {
        $('#serversGrowthChange').removeClass();
        $('#serversGrowthChange').addClass('growthMetricPositive');
        $('#serversGrowthChange').text(
          'Change: +' + (currentServers - beginningOfYearServers),
        );
      } else if (currentServers == beginningOfYearServers) {
        $('#serversGrowthChange').removeClass();
        $('#serversGrowthChange').addClass('growthMetricNeutral');
        $('#serversGrowthChange').text('No change');
      } else {
        $('#serversGrowthChange').removeClass();
        $('#serversGrowthChange').addClass('growthMetricNegative');
        $('#serversGrowthChange').text(
          'Change: -' + (beginningOfYearServers - currentServers),
        );
      }
    },
  };
});
