import React from 'react';
import { Card, Col, Icon, Row, Statistic } from 'antd';
import axios from 'axios';

const colors = {
  success: '#3f8600',
  failure: '#cf1322',
};

class PingStats extends React.Component {
  state = {
    pingTimeMillis: undefined,
    pingSuccess: undefined,
    pingError: undefined,
  };

  _pingInterval = undefined;

  _onPing = async () => {
    const pingStart = new Date();

    let pingSuccess, pingError;
    try {
      await axios.get(`${this.props.settings.serverEndpoint}/healthcheck/ping`);
      pingSuccess = true;
    } catch (e) {
      pingError = e.message || e.response.data;
      pingSuccess = false;
    }

    this.setState({
      pingTimeMillis: new Date() - pingStart,
      pingSuccess,
      pingError,
    });
  };

  async componentDidMount() {
    await this._onPing();
    this._pingInterval = setInterval(this._onPing, this.props.settings.pingIntervalSeconds * 1000);
  }

  componentWillUnmount() {
    if (this._pingInterval != null) {
      clearInterval(this._pingInterval);
    }
  }

  render() {
    return (
      <Row gutter={16}>
        <Col span={6}>
          <Card loading={this.state.pingTimeMillis == null}>
            <Statistic
              title="Ping time"
              value={this.state.pingTimeMillis}
              suffix="ms"
              valueStyle={{ color: this.state.pingTimeMillis <= this.props.settings.pingMaxLatencyMillis
                ? colors.success : colors.failure }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={this.state.pingSuccess == null}>
            <Statistic
              title="Ping status"
              value={this.state.pingSuccess ? 'Ok' : this.state.pingError }
              prefix={this.state.pingSuccess ? undefined : <Icon type="warning" />}
              valueStyle={{ color: this.state.pingSuccess ? colors.success : colors.failure }}
            />
          </Card>
        </Col>
      </Row>
    );
  }
}

export default PingStats;
