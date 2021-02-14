import React, { Component } from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';
import Datetime from 'react-datetime';
import {
  propTypes,
  defaultProps,
} from '../components/DatetimeRangePicker.react.js';

export default class DatetimeRangePicker extends Component {
  constructor(props) {
    super(props);

    this.state = {
      start: moment(props.start),
      end: moment(props.end),
    };

  }

  baseProps() {
    return {
      utc: this.props.utc,
      locale: this.props.locale,
      input: !this.props.inline,
      viewMode: this.props.viewMode,
      dateFormat: this.props.dateFormat,
      timeFormat: this.props.timeFormat,
      closeOnTab: this.props.closeOnTab,
      className: this.props.pickerClassName,
      closeOnSelect: this.props.closeOnSelect,
    };
  }

  startDateProps() {
    let inputProps = {...this.props.inputProps};
    inputProps.title = 'Pick a start date';

    return {
      ...this.baseProps(),
      inputProps: inputProps,
      value: this.state.start,
      onBlur: this.props.onStartDateBlur,
      onFocus: this.props.onStartDateFocus,
      timeConstraints: this.props.startTimeConstraints,
      ref: "startDateRef", // use the Imperative API feature in this.onFocus()
    };
  }

  endDateProps() {
    let inputProps = {...this.props.inputProps};
    inputProps.title = 'Pick an end date';

    return {
      ...this.baseProps(),
      inputProps: inputProps,
      value: this.state.end,
      onBlur: this.props.onEndDateBlur,
      onFocus: this.props.onEndDateFocus,
      timeConstraints: this.props.endTimeConstraints,
      ref: "endDateRef", // use the Imperative API feature in this.onFocus()
    };
  }

  isValidDate( date ) {
    if ( (this.props.min_date && date.isBefore(this.props.min_date, 'day')) ||
         (this.props.max_date && date.isAfter(this.props.max_date, 'day')) ) {
      return false;
    }
    return true;
  }

  onStartDateChange( date ) {
    let state = {start: date, end: this.state.end};
    if (this.state.end.isBefore(date)) {
       state.start = moment.min(this.state.end, this.state.start);
       state.end = date;
    }
    this.setState(state, () => {
      this.props.onStartDateChange(state.start.toDate());
      this.props.onEndDateChange(state.end.toDate());
    });
  }

  onEndDateChange( date ) {
    let state = {start: this.state.start, end: date};
    if (this.state.start.isAfter(date)) {
       state.start = date;
       state.end = moment.max(this.state.end, this.state.start);
    }
    this.setState(state, () => {
      this.props.onStartDateChange(state.start.toDate());
      this.props.onEndDateChange(state.end.toDate());
    });
  }

  onClose( date ) {
    this.props.onStartEndClose({
      start: this.state.start.toDate(),
      end: this.state.end.toDate()
    });
  }

  onFocus() {
    this.refs.startDateRef.setViewDate(this.state.start);
    this.refs.endDateRef.setViewDate(this.state.end);
  }

  onNowButtonClick() {
    let state = {start: this.state.start, end: moment(new Date())};
    if (this.state.start.isAfter(state.end)) {
      state.start = state.end;
    }
    this.setState(state, () => {
      this.props.onStartEndClose({
        start: this.state.start.toDate(),
        end: this.state.end.toDate()
      });
    });
  }

  renderDay( dayProps, date, selectedDate ) {
    const { start, end } = this.state;
    const { className, ...rest } = dayProps;

    // use the CSS style for the dates in the range between the selected dates
    let classes = date.isBetween(start, end)
      ? `${dayProps.className} in-selecting-range`
      : dayProps.className;

    // use the CSS style for the selected start and end dates in the calendar
    classes = date.isSame(start, 'day') || date.isSame(end, 'day')
      ? `${classes} rdtActive`
      : classes;

    return (
      <td {...rest} className={classes}>
        {date.date()}
      </td>
    );
  }

  renderInput( props, openCalendar, closeCalendar ) {
    const datetime = moment(props.value);

    const DateStyle = {
      ...this.props.date_style,
    };

    const TimeStyle = {
      ...this.props.time_style,
    };

    return (
        <button
          type="button"
          className="datetime-range-input"
          onClick={openCalendar}
          title={props.title}
        >
          <span style={DateStyle}>
            {datetime.format(this.props.date_format)}
          </span>
          <br/>
          <span style={TimeStyle}>
            {datetime.format(this.props.time_format)}
          </span>
        </button>
    );
  }

  render() {
    const {color, ...svg} = this.props.arrow

    // Convert <br> tags into valid HTML for the <button> text
    // To avoid get the following warning
    //   Warning: Each child in a list should have a unique "key" prop.
    // we use <div key={a}></div> in el.concat() instead of using <br/>
    let arr = this.props.text.split(/<br\s*\/?>/i);
    const text = arr.reduce((el, a) => el.concat(a, <div key={a}></div>), []);

    return (
      <div
        className={"datetime-range " + this.props.class_name}
        onFocus={this.onFocus.bind(this)}
      >
        <Datetime
          {...this.startDateProps()}
          isValidDate={this.isValidDate.bind(this)}
          onChange={this.onStartDateChange.bind(this)}
          renderDay={this.renderDay.bind(this)}
          renderInput={this.renderInput.bind(this)}
          onClose={this.onClose.bind(this)}
        />

        <div>
          <svg focusable="false" viewBox="0 0 1280 640" {...svg} >
            <g transform="translate(0, 640) scale(0.1,-0.1)" fill={color} >
              <path d="M9280 5934 c-106 -21 -223 -80 -293 -150 -99 -97 -148 -196 -168
              -336 -10 -72 -9 -97 5 -164 22 -108 75 -212 144 -282 33 -33 391 -297 851
              -627 l794 -570 -5084 -5 c-4763 -5 -5087 -6 -5132 -22 -146 -52 -265 -152
              -330 -275 -114 -217 -77 -472 93 -644 70 -71 126 -108 217 -142 l58 -22 5078
              -5 5078 -5 -752 -615 c-414 -338 -776 -638 -804 -667 -29 -29 -68 -84 -89
              -125 -112 -224 -73 -470 105 -649 104 -105 233 -159 382 -159 99 0 186 22 270
              68 70 39 2847 2303 2942 2399 160 162 199 422 93 633 -46 94 -119 163 -324
              311 -1086 782 -2701 1940 -2747 1970 -83 54 -166 80 -272 84 -49 2 -101 1
              -115 -1z"/>
            </g>
          </svg>
        </div>

        <Datetime
          {...this.endDateProps()}
          isValidDate={this.isValidDate.bind(this)}
          onChange={this.onEndDateChange.bind(this)}
          renderDay={this.renderDay.bind(this)}
          renderInput={this.renderInput.bind(this)}
          onClose={this.onClose.bind(this)}
        />

        <button
          type="button"
          className="datetime-range-now-button"
          title="Set the end date to be the current date and time"
          onClick={this.onNowButtonClick.bind(this)}
        >
        {text}
        </button>

      </div>
    );
  }
}

DatetimeRangePicker.defaultProps = {
  ...defaultProps,
  utc: false,
  locale: null,
  input: false,
  inline: false,
  className: '',
  viewMode: 'days',
  dateFormat: 'YYYY-MM-DD',
  timeFormat: 'HH:mm:ss',
  closeOnTab: true,
  onBlur: () => {},
  onFocus: () => {},
  onChange: () => {},
  pickerClassName: '',
  closeOnSelect: false,
  inputProps: undefined,
  onEndDateBlur: () => {},
  endTimeConstraints: {},
  onEndDateFocus: () => {},
  isValidStartDate: () => true,
  isValidEndDate: () => true,
  onStartDateBlur: () => {},
  onEndDateChange: () => {},
  onStartDateFocus: () => {},
  startTimeConstraints: {},
  onStartDateChange: () => {},
};

DatetimeRangePicker.propTypes = {
  ...propTypes,
  /**
   * When true, start and end time values will be interpreted as UTC.
   * Otherwise they will default to the user's local timezone.
   */
  utc: PropTypes.bool,
  /**
   * This defines whether or not to allow user to manually edit date via input field.
   */
  input: PropTypes.bool,
  /**
   * If set to true will render start date and end date with calender without input fields.
   */
  inline: PropTypes.bool,
  /**
   * This callback is triggered when user clicks outside the datetime range picker.
   * The callback receives an object with the selected start and date date as only parameter.
   */
  onBlur: PropTypes.func,
  /**
   * This callback is triggered when user clicks anywhere inside the outermost element of the picker.
   */
  onFocus: PropTypes.func,
  /**
   * Manually set the locale.
   */
  locale: PropTypes.string,
  /**
   * This callback is triggered everytime a user selects a start date or an end date from the picker.
   */
  onChange: PropTypes.func,
  /**
   * This defines the default view to display when the pickers are shown. ('years', 'months', 'days', 'time').
   */
  viewMode: PropTypes.oneOf(["years", "months", "days", "time"]),
  /**
   * When true and the input is focused, pressing the tab key will close the datepicker.
   */
  closeOnTab: PropTypes.bool,
  /**
   * CSS class(es) for the outermost markup element.
   */
  className: PropTypes.string,
  /**
   * Defines additional attributes for the input element of the component.
   * For example: placeholder, disabled, required, name and className (className sets the class attribute for the input element).
   * This applies to both the start and end datetime inputs
   */
  inputProps: PropTypes.object, // eslint-disable-line
  /**
   * When true, once the day has been selected, the datepicker will be automatically closed.
   * This is useful when using this as a date range picker instead of datetime range picker.
   */
  closeOnSelect: PropTypes.bool,
  /**
   * Define the dates that can be selected in the end date picker.
   * The function receives (currentDate, selectedDate) and shall return a true or false whether the currentDate is valid or not.
   */
  isValidEndDate: PropTypes.func,
  /**
   * Define the dates that can be selected in the start date picker.
   * The function receives (currentDate, selectedDate) and shall return a true or false whether the currentDate is valid or not.
   */
  isValidStartDate: PropTypes.func,
  /**
   * Callback is triggered when user clicks outside the end date input.
   * The callback receives the selected moment object as only parameter, if the date in the input is valid.
   * If the date in the input is not valid, the callback returned.
   */
  onEndDateBlur: PropTypes.func,
  /**
   * Callback trigger for when the user opens the end date datepicker.
   */
  onEndDateFocus: PropTypes.func,
  /**
   * This callback is triggered everytime the end date changes.
   * It receives the selected date as the only parameter.
   */
  onEndDateChange: PropTypes.func,
  /**
   * This callback is triggered when user clicks outside of the start date input.
   * The callback receives the selected start date as the a parameter
   */
  onStartDateBlur: PropTypes.func,
  /**
   * Callback trigger for when the user opens the start date datepicker.
   */
  onStartDateFocus: PropTypes.func,
  /**
   * Callback trigger for when start date changes.
   * This callback receives selected moment object as a parameter.
   */
  onStartDateChange: PropTypes.func,
  /**
   * CSS class to attach to outer div that wraps the individual pickers.
   * This class is applied to both the start and end pickers.
   * This is particular useful if you want to add col-*.
   */
  pickerClassName: PropTypes.string,
  /**
   * Add some constraints to the end timepicker.
   * It accepts an object with the format { hours: { min: 9, max: 15, step: 2 }},
   * this example means the hours can't be lower than 9 and higher than 15,
   * and it will change adding or subtracting 2 hours everytime the buttons are clicked.
   * The constraints can be added to the hours, minutes, seconds and milliseconds.
   */
  endTimeConstraints: PropTypes.object, // eslint-disable-line
  /**
   * Add some constraints to the start timepicker.
   * It accepts an object with the format { hours: { min: 9, max: 15, step: 2 }},
   * this example means the hours can't be lower than 9 and higher than 15,
   * and it will change adding or subtracting 2 hours everytime the buttons are clicked.
   * The constraints can be added to the hours, minutes, seconds and milliseconds.
   */
  startTimeConstraints: PropTypes.object, // eslint-disable-line
  /**
   * Defines the format for the date.
   * It accepts any Moment date format (not in localized format).
   * If true the date will be displayed using the defaults for the current locale.
   * If false the datepicker is disabled and the component can be used as timepicker.
   */
  dateFormat: PropTypes.oneOfType([PropTypes.bool, PropTypes.string]),
  /**
   * Defines the format for the time.
   * It accepts any Moment time format (not in localized format).
   * If true the time will be displayed using the defaults for the current locale.
   * If false the timepicker is disabled and the component can be used as datepicker.
   */
  timeFormat: PropTypes.oneOfType([PropTypes.bool, PropTypes.string]),
};