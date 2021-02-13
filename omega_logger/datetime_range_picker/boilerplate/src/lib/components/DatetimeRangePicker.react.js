import React, { Component } from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';
import DatetimeRangePicker from '../utils/DatetimeRangePicker.jsx';

/**
 * Select a range of dates to within millisecond resolution.
 *
 * Based off of https://github.com/SebastianRehfeldt/dash-datepicker
 */
export default class DatetimeRangeWrapper extends Component {

  toPythonISOString(date) {
    // allows for using datetime.fromisoformat() for the
    // dash.dependencies.Input parameter in the callback
    function pad(number) {
      if (number < 10) {
        return '0' + number;
      }
      return number;
    }
    return date.getFullYear() +
      '-' + pad(date.getMonth() + 1) +
      '-' + pad(date.getDate()) +
      'T' + pad(date.getHours()) +
      ':' + pad(date.getMinutes()) +
      ':' + pad(date.getSeconds())
  }

  componentDidMount() {
    this.props.setProps({
      start: this.toPythonISOString(moment(this.props.start).toDate()),
      end: this.toPythonISOString(moment(this.props.end).toDate())
    });
  }

  render() {
    return (
      <DatetimeRangePicker
        {...this.props}
        //onEndDateChange={(e) =>
        //  this.props.setProps({ end: this.toPythonISOString(e) })
        //}
        //onStartDateChange={(e) =>
        //  this.props.setProps({ start: this.toPythonISOString(e) })
        //}
        onEndDateClose={(e) =>
          this.props.setProps({ end: this.toPythonISOString(e) })
        }
        onStartDateClose={(e) =>
          this.props.setProps({ start: this.toPythonISOString(e) })
        }
      />
    );
  }

}

DatetimeRangeWrapper.defaultProps = {
  start: new Date((new Date()).setHours(8, 0, 0, 0) - 1000 * 60 * 60 * 24),
  end: new Date(),
  min_date: null,
  max_date: null,
  date_format: 'YYYY-MM-DD',
  time_format: 'HH:mm:ss',
  date_style: undefined,
  time_style: undefined,
  arrow: {
    width: '30px',
    height: '35px',
    color: 'black',
  },
  class_name: 'datetime-range-center',
  text: 'Update<br/>end date',
};

DatetimeRangeWrapper.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

  /**
   * The start date of the range picker. Use the ISO 8601 format
   * ``yyyy-mm-dd`` or ``yyyy-mm-dd HH:MM:SS`` for a string. A Dash
   * callback is triggered when the range picker closes.
   */
  start: PropTypes.oneOfType([
    PropTypes.instanceOf(moment),
    PropTypes.instanceOf(Date),
    PropTypes.string,
  ]),

  /**
   * The end date of the range picker. Use the ISO 8601 format
   * ``yyyy-mm-dd`` or ``yyyy-mm-dd HH:MM:SS`` for a string. A Dash
   * callback is triggered when the range picker closes.
   */
  end: PropTypes.oneOfType([
    PropTypes.instanceOf(moment),
    PropTypes.instanceOf(Date),
    PropTypes.string,
  ]),

  /**
   * The minimum date that can be picked.
   */
  min_date: PropTypes.string,

  /**
   * The maximum date that can be picked.
   */
  max_date: PropTypes.string,

  /**
   * The format to use to display the date that was picked.
   * See :ref:`https://www.tutorialspoint.com/momentjs/momentjs_format.htm`
   * for supported formats.
   */
  date_format: PropTypes.string,

  /**
   * The format to use to display the time that was picked.
   * See :ref:`https://www.tutorialspoint.com/momentjs/momentjs_format.htm`
   * for supported formats.
   */
  time_format: PropTypes.string,

  /**
   * The style to use to render the date that was picked.
   */
  date_style: PropTypes.object,

  /**
   * The style to use to render the time that was picked.
   */
  time_style: PropTypes.object,

  /**
   * The SVG properties of the arrow.
   */
  arrow: PropTypes.object,

  /**
   * A class name in the ``datetime_range_picker.css`` file.
   */
  class_name: PropTypes.string,

  /**
   * The text to display to the user to update the end date to the
   * current date and time. Use the ``<br/>`` tag to insert a line break.
   */
  text: PropTypes.string,

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func,

};

export const propTypes = DatetimeRangeWrapper.propTypes;
export const defaultProps = DatetimeRangeWrapper.defaultProps;
