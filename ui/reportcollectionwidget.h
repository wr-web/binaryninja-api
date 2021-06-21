#pragma once

#include "binaryninjaapi.h"
#include "uicontext.h"
#include "viewframe.h"
#include <QtWidgets/QListWidget>
#include <QtWidgets/QSplitter>
#include <QtWidgets/QVBoxLayout>
#include <QtWidgets/QWidget>

class BINARYNINJAUIAPI ReportCollectionWidget : public QWidget, public ViewContainer
{
	Q_OBJECT

	QSplitter* m_splitter;
	QListWidget* m_list;
	QWidget* m_report;
	QWidget* m_reportContainer;
	QVBoxLayout* m_reportLayout;

	ReportCollectionRef m_collection;
	int m_currentReportIndex;
	std::string m_title;

 public:
	ReportCollectionWidget(QWidget* parent, ReportCollectionRef reports, const std::string& title);

	virtual View* getView() override;

 private Q_SLOTS:
	void selectReport(int i);
};
