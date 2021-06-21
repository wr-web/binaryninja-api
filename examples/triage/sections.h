#pragma once

#include "uitypes.h"
#include <QtWidgets/QWidget>


class SegmentsWidget : public QWidget
{
	std::vector<SegmentRef> m_segments;

 public:
	SegmentsWidget(QWidget* parent, BinaryViewRef data);
	const std::vector<SegmentRef>& GetSegments() const { return m_segments; }
};


class SectionsWidget : public QWidget
{
	std::vector<SectionRef> m_sections;

 public:
	SectionsWidget(QWidget* parent, BinaryViewRef data);
	const std::vector<SectionRef>& GetSections() const { return m_sections; }
};
